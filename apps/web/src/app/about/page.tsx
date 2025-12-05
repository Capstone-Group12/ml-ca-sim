import { Card, CardContent, Typography, Link as MuiLink } from "@mui/material";

const team = [
  { name: "Edward Nafornita", role: "Project Lead", bio: "Coordinates development and ML integration.", contact: "naforni@uwindsor.ca" },
  { name: "Gordon Horway", role: "Backend Lead", bio: "Designs backend integrations.", contact: "horwayg@uwindsor.ca" },
  { name: "Dane St John", role: "Frontend Lead", bio: "Builds the UI and visualizations.", contact: "stjohn3@uwindsor.ca" },
  { name: "Sarah Bellaire", role: "ML Lead", bio: "Designs and trains ML models.", contact: "bellair5@uwindsor.ca" },
  { name: "Brandon Levack", role: "QA/Testing Lead", bio: "Creates the attack simulations.", contact: "levack1@uwindsor.ca" },
];

export default function About() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-12 text-white">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-semibold">Meet the Team</h1>
        <p className="mt-2 text-slate-200">
          Five builders behind the ML cyberattack simulation.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {team.map((p) => (
          <Card
            key={p.name}
            sx={{
              background: "linear-gradient(135deg, rgba(24,30,48,0.95), rgba(15,18,30,0.95))",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "#e2e8f0",
              boxShadow: "0 12px 28px rgba(0,0,0,0.4)",
              height: "100%",
              width: "100%",
            }}
          >
            <CardContent sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
              <div>
                <Typography variant="h6" component="div" sx={{ color: "#f8fafc" }}>
                  {p.name}
                </Typography>
                <Typography variant="caption" sx={{ color: "#cbd5f5" }}>
                  {p.role}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1.5, color: "#cbd5f5" }}>
                  {p.bio}
                </Typography>
              </div>
              <MuiLink
                href={`mailto:${p.contact}`}
                sx={{ display: "inline-block", mt: "auto", pt: 2, color: "#a3c5ff" }}
              >
                Email
              </MuiLink>
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}
