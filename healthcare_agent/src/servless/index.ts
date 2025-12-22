import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// --- CORS Headers ---
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// --- TypeScript Interface for an Appointment (using lowercase keys to match DB) ---
interface Appointment {
  appointmentid: string;
  patientname: string;
  doctorname: string;
  date: string;
  time: string;
  summaryfordoctor?: string;
  consultationsummary?: string;
}

serve(async (req) => {
  // Handle preflight requests for CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get("URL") ?? "",
      Deno.env.get("ANON_KEY") ?? "",
      { global: { headers: { Authorization: req.headers.get("Authorization")! } } }
    );

    const url = new URL(req.url);
    const pathname = url.pathname;

    // --- Routing ---

    // Root endpoint: matches /index or /
    if (pathname === "/index" || pathname === "/") {
      return new Response(JSON.stringify({ message: "Welcome to the Appointments API" }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // Path for all appointments
    const appointmentsPath = "/index/appointments";

    // GET /index/appointments
    if (pathname === appointmentsPath && req.method === "GET") {
      const { data, error } = await supabase.from("appointments").select("*");
      if (error) throw error;
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // POST /index/appointments
    if (pathname === appointmentsPath && req.method === "POST") {
      const appointment: Appointment = await req.json();
      if (!appointment.patientname || !appointment.doctorname) {
        return new Response(JSON.stringify({ error: "patientname and doctorname are required." }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        });
      }

      const { data, error } = await supabase.from("appointments").insert(appointment).select().single();
      if (error) throw error;

      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 201,
      });
    }

    // PUT /index/appointments/{appointment_id}
    const updateMatch = pathname.match(/^\/index\/appointments\/([^\/]+)$/);
    if (updateMatch && req.method === "PUT") {
      const appointmentId = updateMatch[1];
      const updates: Partial<Appointment> = await req.json();

      const { data, error } = await supabase
        .from("appointments")
        .update(updates)
        .eq("appointmentid", appointmentId)
        .select()
        .single();

      if (error) throw error;
      if (!data) {
        return new Response(JSON.stringify({ error: "Appointment not found" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 404,
        });
      }

      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // GET /index/appointments/{appointment_id}/summary
    const summaryMatch = pathname.match(/^\/index\/appointments\/([^\/]+)\/summary$/);
    if (summaryMatch && req.method === "GET") {
      const appointmentId = summaryMatch[1];
      const { data, error } = await supabase
        .from("appointments")
        .select("summaryfordoctor")
        .eq("appointmentid", appointmentId)
        .single();

      if (error) throw error;
      if (!data) {
         return new Response(JSON.stringify({ error: "Appointment not found" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 404,
        });
      }

      return new Response(JSON.stringify({ summary: data.summaryfordoctor }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // GET /index/appointments/{appointment_id}/consultationsummary
    const consultationSummaryMatch = pathname.match(/^\/index\/appointments\/([^\/]+)\/consultationsummary$/);
    if (consultationSummaryMatch && req.method === "GET") {
      const appointmentId = consultationSummaryMatch[1];
      const { data, error } = await supabase
        .from("appointments")
        .select("consultationsummary")
        .eq("appointmentid", appointmentId)
        .single();

      if (error) throw error;
      if (!data) {
        return new Response(JSON.stringify({ error: "Appointment not found" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 404,
        });
      }

      return new Response(JSON.stringify({ consultationsummary: data.consultationsummary }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // --- Fallback for unmatched routes ---
    return new Response(JSON.stringify({ error: "Not Found", path: pathname }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 404,
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: (error as Error).message }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 500,
    });
  }
});
