import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional, Tuple, Union
from email.message import EmailMessage
from email import message_from_bytes


class GmailImapParser:
    """A class to handle Gmail IMAP operations and email parsing."""
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize the Gmail parser.
        
        Args:
            email_address: Gmail address
            app_password: Gmail app password
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None
    
    def connect(self, folder: str = "INBOX", verbose: bool = False) -> bool:
        """
        Connect to Gmail IMAP server.
        
        Args:
            folder: Gmail folder/label to select (default: "INBOX")
            verbose: If True, print connection info
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap.login(self.email_address, self.app_password)
            
            # Quote folder name if it contains special characters or spaces
            if ' ' in folder or '[' in folder or ']' in folder or '/' in folder:
                quoted_folder = f'"{folder}"'
            else:
                quoted_folder = folder
            
            self.imap.select(quoted_folder)
            if verbose:
                print(f"Connected to Gmail folder: {folder}")
            return True
        except Exception as e:
            if verbose:
                print(f"Failed to connect to {folder}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
            except (OSError, Exception) as e:
                # Handle socket errors and other connection issues gracefully
                try:
                    self.imap.close()
                except:
                    pass
            finally:
                self.imap = None
    
    def get_search_criteria(self, 
                           start_date: Optional[Union[datetime, str]] = None,
                           end_date: Optional[Union[datetime, str]] = None,
                           days: Optional[int] = None,
                           hours: Optional[int] = None,
                           minutes: Optional[int] = None,
                           search_all: bool = False,
                           unread_only: bool = False,
                           from_email: Optional[str] = None) -> str:
        """
        Generate search criteria for emails with flexible time options.
        
        Args:
            start_date: Start date (datetime object or string in format 'DD-Mon-YYYY')
            end_date: End date (datetime object or string in format 'DD-Mon-YYYY')
            days: Number of days to look back from now
            hours: Number of hours to look back from now  
            minutes: Number of minutes to look back from now
            search_all: If True, search all emails
            unread_only: If True, only search unread emails
            
            from_email: Email address to search for in the From field
            
        Returns:
            str: IMAP search criteria
            
        Examples:
            # Last 3 days, unread only
            get_search_criteria(days=3, unread_only=True)
            
            # Last 6 hours
            get_search_criteria(hours=6)
            
            # Since specific date
            get_search_criteria(start_date=datetime(2025, 6, 1))
            
            # Date range, unread only
            get_search_criteria(start_date='01-Jun-2025', end_date='10-Jun-2025', unread_only=True)
            
            # Emails from specific sender in last 7 days
            get_search_criteria(days=7, from_email='sender@example.com')
        """
        if search_all and not unread_only:
            return "ALL"
        
        criteria_parts = []
        
        # Add unread filter if requested
        if unread_only:
            criteria_parts.append("UNSEEN")
        
        # Add from email filter if requested
        if from_email:
            # Remove quotes and handle case sensitivity for more flexible matching
            criteria_parts.append(f'FROM {from_email}')
        
        # Handle relative time arguments (days, hours, minutes)
        if any([days, hours, minutes]):
            total_minutes = 0
            if days:
                total_minutes += days * 24 * 60
            if hours:
                total_minutes += hours * 60
            if minutes:
                total_minutes += minutes
            
            start_datetime = datetime.now() - timedelta(minutes=total_minutes)
            start_date_str = start_datetime.strftime("%d-%b-%Y")
            criteria_parts.append(f'SINCE {start_date_str}')
        
        # Handle explicit start_date
        elif start_date:
            if isinstance(start_date, datetime):
                start_date_str = start_date.strftime("%d-%b-%Y")
            else:
                start_date_str = start_date
            criteria_parts.append(f'SINCE {start_date_str}')
        
        # Default to last 7 days if no time criteria specified and not search_all
        elif not search_all:
            default_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            criteria_parts.append(f'SINCE {default_date}')
        
        # Handle before_date
        if end_date:
            if isinstance(end_date, datetime):
                end_date_str = end_date.strftime("%d-%b-%Y")
            else:
                end_date_str = end_date
            criteria_parts.append(f'BEFORE {end_date_str}')
        
        # Combine criteria
        if len(criteria_parts) == 0:
            return "ALL"
        elif len(criteria_parts) == 1:
            return criteria_parts[0]
        else:
            return f'({" ".join(criteria_parts)})'
    
    def search_emails(self, search_criteria: str, use_uid: bool = True, verbose: bool = False) -> List[bytes]:
        """
        Search for emails based on criteria.
        
        Args:
            search_criteria: IMAP search criteria
            use_uid: If True, use UID search which can be more reliable for threading
            verbose: If True, print search details
            
        Returns:
            List[bytes]: List of email IDs or UIDs
        """
        if not self.imap:
            raise Exception("Not connected to IMAP server")
        
        if verbose:
            print(f"Executing IMAP search with criteria: {search_criteria}")
        
        if use_uid:
            # UID search can be more reliable with Gmail threading
            status, messages = self.imap.uid('search', None, search_criteria)
        else:
            status, messages = self.imap.search(None, search_criteria)
            
        if status != "OK":
            raise Exception(f"Search failed: {status}")
        
        return messages[0].split() if messages[0] else []
    
    def debug_search_comparison(self, 
                               start_date: Optional[Union[datetime, str]] = None,
                               end_date: Optional[Union[datetime, str]] = None,
                               days: Optional[int] = None,
                               hours: Optional[int] = None,
                               minutes: Optional[int] = None,
                               from_email: Optional[str] = None) -> Dict:
        """
        Compare search results with and without FROM filter to help debug missing emails.
        
        Returns:
            Dict: Comparison results showing different search outcomes
        """
        if not self.connect():
            return {}
        
        try:
            # Search without FROM filter
            search_criteria_no_from = self.get_search_criteria(
                start_date=start_date,
                end_date=end_date,
                days=days,
                hours=hours,
                minutes=minutes,
                search_all=False,
                unread_only=False
            )
            emails_no_from = self.search_emails(search_criteria_no_from)
            
            # Search with FROM filter if provided
            emails_with_from = []
            if from_email:
                search_criteria_with_from = self.get_search_criteria(
                    start_date=start_date,
                    end_date=end_date,
                    days=days,
                    hours=hours,
                    minutes=minutes,
                    search_all=False,
                    unread_only=False,
                    from_email=from_email
                )
                emails_with_from = self.search_emails(search_criteria_with_from)
            
            # Parse a few emails from the no_from search to see their from addresses
            sample_emails = []
            for i, email_id in enumerate(emails_no_from[:10]):  # Sample first 10
                email_data = self.parse_single_email(email_id, keep_unread=True, use_uid=True)
                if email_data:
                    sample_emails.append({
                        'uid': email_data.get('uid'),
                        'from': email_data['from'],
                        'subject': email_data['subject'],
                        'timestamp': email_data['timestamp']
                    })
            
            return {
                'search_criteria_no_from': search_criteria_no_from,
                'search_criteria_with_from': search_criteria_with_from if from_email else None,
                'total_emails_no_from': len(emails_no_from),
                'total_emails_with_from': len(emails_with_from),
                'sample_email_from_addresses': sample_emails
            }
        
        finally:
            self.disconnect()
    
    def fetch_emails_comprehensive(self, 
                                  start_date: Optional[Union[datetime, str]] = None,
                                  end_date: Optional[Union[datetime, str]] = None,
                                  days: Optional[int] = None,
                                  hours: Optional[int] = None,
                                  minutes: Optional[int] = None,
                                  from_email: Optional[str] = None,
                                  unread_only: bool = False,
                                  keep_unread: bool = True) -> List[Dict]:
        """
        Comprehensive email fetch with multiple search strategies.
        
        NOTE: The regular fetch_emails() method now searches INBOX and Important folders 
        by default, so this comprehensive method is mainly for edge cases.
        
        Args:
            start_date: Start date (datetime object or string in format 'DD-Mon-YYYY')
            end_date: End date (datetime object or string in format 'DD-Mon-YYYY')
            days: Number of days to look back from now
            hours: Number of hours to look back from now
            minutes: Number of minutes to look back from now
            from_email: Email address to search for in the From field
            unread_only: If True, only fetch unread emails
            keep_unread: If True, don't mark emails as read
            
        Returns:
            List[Dict]: List of parsed email data with duplicates removed
        """
        # For most cases, the regular fetch_emails with search_all_folders=True is sufficient
        return self.fetch_emails(
            start_date=start_date,
            end_date=end_date,
            days=days,
            hours=hours,
            minutes=minutes,
            from_email=from_email,
            unread_only=unread_only,
            keep_unread=keep_unread,
            verbose=True,  # Comprehensive method should be verbose
            search_all_folders=True
        )
    
    def decode_header_value(self, header_value: str) -> str:
        """
        Decode email header value.
        
        Args:
            header_value: Raw header value
            
        Returns:
            str: Decoded header value
        """
        if not header_value:
            return ""
        
        decoded, encoding = decode_header(header_value)[0]
        if isinstance(decoded, bytes):
            return decoded.decode(encoding or "utf-8", errors="ignore")
        return decoded
    
    def extract_uid(self, email_id: bytes) -> Optional[str]:
        """
        Extract UID from email ID.
        
        Args:
            email_id: Email ID bytes
            
        Returns:
            Optional[str]: UID if found, None otherwise
        """
        try:
            status, uid_data = self.imap.fetch(email_id, '(UID)')
            if status == "OK" and uid_data:
                response_part = uid_data[0]
                if isinstance(response_part, bytes):
                    match = re.search(r'UID (\d+)', response_part.decode())
                    if match:
                        return match.group(1)
        except Exception as e:
            # Note: This is an internal method, so we don't add verbose control here
            # as it would require passing verbose through many call chains
            return None
    
    def extract_email_body(self, msg: EmailMessage) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract plain text and HTML body from email message.
        
        Args:
            msg: Email message object
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (plain_text_body, html_body)
        """
        plain_body = None
        html_body = None
        
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if "attachment" in content_disposition:
                continue
            
            try:
                body = part.get_payload(decode=True)
                if not body:
                    continue
                
                charset = part.get_content_charset() or "utf-8"
                decoded_body = body.decode(charset, errors="ignore")
                
                if content_type == "text/plain" and not plain_body:
                    plain_body = decoded_body
                elif content_type == "text/html" and not html_body:
                    html_body = decoded_body
                    
            except Exception as e:
                # Note: This is an internal method, so we don't add verbose control here
                continue
        
        return plain_body, html_body
    
    def parse_single_email(self, email_id: bytes, keep_unread: bool = True, use_uid: bool = True, verbose: bool = False) -> Optional[Dict]:
        """
        Parse a single email by ID.
        
        Args:
            email_id: Email ID or UID to parse
            keep_unread: If True, don't mark email as read
            use_uid: If True, treat email_id as UID
            verbose: If True, print parsing details
            
        Returns:
            Optional[Dict]: Parsed email data or None if failed
        """
        try:
            # Use BODY.PEEK to avoid marking as read
            fetch_command = "(BODY.PEEK[])" if keep_unread else "(RFC822)"
            
            if use_uid:
                status, msg_data = self.imap.uid('fetch', email_id, fetch_command)
            else:
                status, msg_data = self.imap.fetch(email_id, fetch_command)
            
            if status != "OK" or not msg_data:
                if verbose:
                    print(f"Failed to fetch email {email_id}")
                return None
            
            # Extract UID - if we're already using UID, this is the UID
            if use_uid:
                uid = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
            else:
                uid = self.extract_uid(email_id)
            
            # Parse email message
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)
            
            # Extract bodies
            plain_body, html_body = self.extract_email_body(msg)
            
            # Build email data dictionary
            email_data = {
                "uid": uid,
                "timestamp": msg.get("Date"),
                "to": msg.get("To"),
                "cc": msg.get("Cc"),
                "bcc": msg.get("Bcc"),
                "from": self.decode_header_value(msg.get("From")),
                "subject": self.decode_header_value(msg.get("Subject")),
            }
            
            if plain_body:
                email_data["body"] = plain_body
            if html_body:
                email_data["html_body"] = html_body
            
            return email_data
            
        except Exception as e:
            if verbose:
                print(f"Failed to parse email {email_id}: {e}")
            return None
    
    def mark_emails_as_read(self, email_ids: List[bytes], verbose: bool = False):
        """
        Mark emails as read.
        
        Args:
            email_ids: List of email IDs to mark as read
            verbose: If True, print status updates
        """
        try:
            for email_id in email_ids:
                self.imap.store(email_id, '+FLAGS', '\\Seen')
        except Exception as e:
            if verbose:
                print(f"Failed to mark emails as read: {e}")
    
    def mark_emails_as_unread(self, email_ids: List[bytes], verbose: bool = False):
        """
        Mark emails as unread.
        
        Args:
            email_ids: List of email IDs to mark as unread
            verbose: If True, print status updates
        """
        try:
            for email_id in email_ids:
                self.imap.store(email_id, '-FLAGS', '\\Seen')
        except Exception as e:
            if verbose:
                print(f"Failed to mark emails as unread: {e}")
    
    def fetch_emails(self, 
                    start_date: Optional[Union[datetime, str]] = None,
                    end_date: Optional[Union[datetime, str]] = None,

                    days: Optional[int] = None,
                    hours: Optional[int] = None,
                    minutes: Optional[int] = None,
                    search_all: bool = False,
                    unread_only: bool = False,
                    keep_unread: bool = True,
                    mark_unread: bool = False,
                    from_email: Optional[str] = None,
                    folder: Optional[str] = None,
                    verbose: bool = False,
                    search_all_folders: bool = False) -> List[Dict]:
        """
        Fetch and parse emails based on flexible time criteria.
        
        Args:
            start_date: Start date (datetime object or string in format 'DD-Mon-YYYY')
            end_date: End date (datetime object or string in format 'DD-Mon-YYYY')
            days: Number of days to look back from now
            hours: Number of hours to look back from now
            minutes: Number of minutes to look back from now
            search_all: If True, search all emails
            unread_only: If True, only fetch unread emails
            keep_unread: If True, don't mark emails as read (use BODY.PEEK)
            mark_unread: If True, mark emails as unread after fetching
            from_email: Email address to search for in the From field
            folder: Specific Gmail folder to search (e.g., "INBOX", "[Gmail]/Important", "[Gmail]/Spam")
            search_all_folders: If True, search INBOX and Important folders (ignored if folder is specified)
            verbose: If True, print verbose output
        Returns:
            List[Dict]: List of parsed email data
            
        Examples:
            # Search specific folder
            fetch_emails(hours=6, folder="[Gmail]/Important")
            fetch_emails(days=2, folder="INBOX")
            
            # Search all key folders (default)
            fetch_emails(days=2, unread_only=True)
            
            # Emails from specific sender in specific folder
            fetch_emails(days=3, from_email='sender@example.com', folder="[Gmail]/Spam")
        """
        if folder:
            # Search specific folder
            return self._search_single_folder(
                folder=folder,
                start_date=start_date,
                end_date=end_date,
                days=days,
                hours=hours,
                minutes=minutes,
                search_all=search_all,
                unread_only=unread_only,
                from_email=from_email,
                keep_unread=keep_unread,
                mark_unread=mark_unread,
                verbose=verbose
            )
        elif search_all_folders:
            # Search across key Gmail folders by default
            return self._search_multiple_folders(
                start_date=start_date,
                end_date=end_date,
                days=days,
                hours=hours,
                minutes=minutes,
                search_all=search_all,
                unread_only=unread_only,
                from_email=from_email,
                keep_unread=keep_unread,
                mark_unread=mark_unread,
                verbose=verbose
            )
        else:
            # Single folder search (INBOX only) - for backwards compatibility
            return self._search_single_folder(
                folder="INBOX",
                start_date=start_date,
                end_date=end_date,
                days=days,
                hours=hours,
                minutes=minutes,
                search_all=search_all,
                unread_only=unread_only,
                from_email=from_email,
                keep_unread=keep_unread,
                mark_unread=mark_unread,
                verbose=verbose
            )
    
    def _search_single_folder(self, folder: str, **kwargs) -> List[Dict]:
        """Search emails in a single folder."""
        verbose = kwargs.get('verbose', False)
        if not self.connect(folder, verbose=verbose):
            return []
        
        try:
            search_criteria = self.get_search_criteria(
                start_date=kwargs.get('start_date'),
                end_date=kwargs.get('end_date'),
                days=kwargs.get('days'),
                hours=kwargs.get('hours'),
                minutes=kwargs.get('minutes'),
                search_all=kwargs.get('search_all', False),
                unread_only=kwargs.get('unread_only', False),
                from_email=kwargs.get('from_email')
            )
            email_ids = self.search_emails(search_criteria, verbose=verbose)
            
            if verbose:
                unread_status = "unread " if kwargs.get('unread_only') else ""
                print(f"Found {len(email_ids)} {unread_status}email(s) in {folder}")
            
            # Parse emails
            parsed_emails = []
            for email_id in email_ids:
                email_data = self.parse_single_email(email_id, kwargs.get('keep_unread', True), use_uid=True, verbose=verbose)
                if email_data:
                    email_data['folder'] = folder
                    parsed_emails.append(email_data)
            
            return parsed_emails
            
        finally:
            self.disconnect()
    
    def _search_multiple_folders(self, **kwargs) -> List[Dict]:
        """Search emails across key Gmail folders and deduplicate results."""
        verbose = kwargs.get('verbose', False)
        # Key Gmail folders to search
        folders_to_search = ["INBOX", "[Gmail]/Important"]
        
        all_emails = {}  # Use UID as key to deduplicate
        
        for folder in folders_to_search:
            try:
                folder_emails = self._search_single_folder(folder, **kwargs)
                
                for email in folder_emails:
                    uid = email.get('uid')
                    if uid and uid not in all_emails:
                        all_emails[uid] = email
                    elif uid in all_emails:
                        # If email exists, prefer the one from INBOX
                        if folder == "INBOX":
                            all_emails[uid]['folder'] = "INBOX"
                        
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not search {folder}: {e}")
                continue
        
        final_emails = list(all_emails.values())
        
        # Sort by timestamp
        try:
            final_emails.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except:
            pass
        
        if verbose:
            print(f"Total unique emails found across folders: {len(final_emails)}")
        
        return final_emails
    
    def debug_all_emails_from_sender(self, from_email: str, limit: int = 20) -> List[Dict]:
        """
        Debug method: Get all recent emails from a specific sender to see timing issues.
        
        Args:
            from_email: Email address to search for
            limit: Maximum number of recent emails to return
            
        Returns:
            List[Dict]: Recent emails from sender with timestamps
        """
        if not self.connect():
            return []
        
        try:
            print(f"DEBUG: Fetching all emails from {from_email}")
            
            # Search for ALL emails from this sender
            search_criteria = f'FROM {from_email}'
            email_ids = self.search_emails(search_criteria, use_uid=True)
            
            print(f"DEBUG: Found {len(email_ids)} total emails from {from_email}")
            
            # Get the most recent emails
            recent_emails = []
            for email_id in email_ids[-limit:]:  # Get last N emails
                email_data = self.parse_single_email(email_id, keep_unread=True, use_uid=True)
                if email_data:
                    recent_emails.append(email_data)
            
            # Sort by timestamp (most recent first)
            try:
                recent_emails.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            except:
                pass
            
            print(f"DEBUG: Showing {len(recent_emails)} most recent emails:")
            for i, email in enumerate(recent_emails):
                print(f"  {i+1}. UID: {email.get('uid')}")
                print(f"     Subject: {email.get('subject')}")
                print(f"     Timestamp: {email.get('timestamp')}")
                print(f"     From: {email.get('from')}")
                print("     ---")
            
            return recent_emails
            
        finally:
            self.disconnect()
    
    def search_all_gmail_folders(self, 
                                hours: Optional[int] = None,
                                days: Optional[int] = None,
                                from_email: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Search for emails across all Gmail folders/labels to find missing emails.
        
        Args:
            hours: Number of hours to look back
            days: Number of days to look back  
            from_email: Email address to search for
            
        Returns:
            Dict[str, List[Dict]]: Results organized by folder name
        """
        # Common Gmail folders that might contain emails
        gmail_folders = [
            "INBOX",
            "[Gmail]/All Mail", 
            "[Gmail]/Sent Mail",
            "[Gmail]/Spam",
            "[Gmail]/Important",
            "INBOX/Security",  # Sometimes Gmail creates subfolders
            "INBOX/Updates"
        ]
        
        results = {}
        
        for folder in gmail_folders:
            try:
                print(f"\n=== Searching folder: {folder} ===")
                
                # Connect to this specific folder
                if not self.connect(folder):
                    print(f"Could not access folder: {folder}")
                    continue
                
                # Search in this folder
                search_criteria = self.get_search_criteria(
                    hours=hours,
                    days=days,
                    from_email=from_email
                )
                
                email_ids = self.search_emails(search_criteria, use_uid=True)
                print(f"Found {len(email_ids)} emails in {folder}")
                
                # Parse emails
                folder_emails = []
                for email_id in email_ids:
                    email_data = self.parse_single_email(email_id, keep_unread=True, use_uid=True)
                    if email_data:
                        email_data['folder'] = folder  # Add folder info
                        folder_emails.append(email_data)
                
                if folder_emails:
                    results[folder] = folder_emails
                    print(f"  Parsed {len(folder_emails)} emails from {folder}")
                    for email in folder_emails:
                        print(f"    UID: {email['uid']}, Subject: {email['subject']}")
                
                self.disconnect()
                
            except Exception as e:
                print(f"Error searching folder {folder}: {e}")
                try:
                    self.disconnect()
                except:
                    pass
                continue
        
        return results
    
    def list_gmail_folders(self, verbose: bool = False) -> List[str]:
        """
        List all available Gmail folders/labels.
        
        Returns:
            List[str]: Available folder names
        """
        try:
            if not self.connect():
                return []
            
            # List all folders
            status, folders = self.imap.list()
            if status == "OK":
                folder_names = []
                for folder in folders:
                    # Parse folder name from IMAP response
                    folder_str = folder.decode() if isinstance(folder, bytes) else str(folder)
                    # Extract folder name (usually the last part after quotes)
                    if '"' in folder_str:
                        folder_name = folder_str.split('"')[-2]
                        folder_names.append(folder_name)
                
                if verbose:
                    print("Available Gmail folders:")
                    for name in folder_names:
                        print(f"  {name}")
                
                return folder_names
            
        except Exception as e:
            print(f"Error listing folders: {e}")
        finally:
            self.disconnect()
        
        return []