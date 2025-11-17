import Link from "next/link";
import { Container, Typography, Card, CardContent, Box, Stack, Button } from "@mui/material";

const team = [
  { name: "Edward Nafornita", role: "Project Lead", bio: "Coordinates development and ML integration."},
  { name: "Gordon Horway", role: "Backend Lead", bio: "Designs backend integrations."},
  { name: "Dane St John", role: "Frontend Lead", bio: "Builds the UI and visualizations."},
  { name: "Sarah Bellaire", role: "ML Lead", bio: "Designs and trains ML models."},
  { name: "Brandon Levack", role: "QA/Testing Lead", bio: "Creates the attack simulations."},
];

export default function About() {
  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h3" gutterBottom>
        About Us
      </Typography>
      <Typography variant="body1" paragraph>
        This project simulates cyberattacks and demonstrates ML-based detection. Meet the team:
      </Typography>

      <Box sx={{ display: "flex", justifyContent: "center", mb: 3 }}>
        <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", justifyContent: "center" }}>
          {team.map((p) => (
            <Card key={p.name} sx={{ width: 220, m: 0, p: 1 }}>
              <CardContent sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
                <Typography variant="subtitle1" align="center">
                  {p.name}
                </Typography>
                <Typography variant="caption" color="text.secondary" align="center">
                  {p.role}
                </Typography>
                <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                  {p.bio}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Box>

      <Box sx={{ textAlign: "center" }}>
        <Button component={Link} href="/contact" variant="contained">
          Contact the Team
        </Button>
      </Box>
    </Container>
  );
}