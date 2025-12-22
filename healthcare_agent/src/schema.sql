CREATE TABLE appointments (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    appointmentId UUID UNIQUE NOT NULL,
    patientName TEXT NOT NULL,
    doctorName TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    summaryForDoctor TEXT,
    consultationSummary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
