import { Container, Typography, Button, Box } from "@mui/material";
import Link from "next/link";

export default function Home() {
  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h3" gutterBottom align="center">
        Welcome to the ML Cyberattack Simulation
      </Typography>
      <Typography variant="body1" paragraph align="center">
        This is the home page built of the Frontend, please click the button below to start the simulation.
      </Typography>

      <Box mt={3}>
        <Button
          variant="contained"
          color="primary"
          component={Link}
          href="/simulation"
        >
          Simulation
        </Button>
      </Box>
    </Container>
  );
}
