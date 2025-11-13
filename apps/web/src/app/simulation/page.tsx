"use client";
import React from "react";
import { Container, Typography, Box, Button, Stack, Paper } from "@mui/material";
import AttackSelector, { AttackType } from "./AttackSelector";
import SimulationResults from "./SimulationResults";
import SimulationControls from "./SimulationControls";

export default function SimulationPage() {
  const [attackType, setAttackType] = React.useState<AttackType>("DDos");
  const [intensity, setIntensity] = React.useState<number>(50);
  const [duration, setDuration] = React.useState<number>(10);
  const [results, setResults] = React.useState<number[]>([]);
  const [running, setRunning] = React.useState(false);

  const runSimulation = () => {
    setRunning(true);

    const seedFactor =
      attackType === "DDos" ? 1.1 : attackType === "Sloworis" ? 0.9 : 1.0;
    const simulated = Array.from({ length: duration }, (_, i) => {
      const base = intensity * seedFactor;
      const trend = base * (1 - i / (duration * 1.5));
      const noise = (Math.random() - 0.5) * 20;
      return Math.max(0, Math.round(trend + noise));
    });

    setResults(simulated);
    setRunning(false);
  };

  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h4" gutterBottom>
        Cyberattack Simulation
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems="center"
        >
          <Box>
            <AttackSelector
              value={attackType}
              onChange={(v) => setAttackType(v)}
            />
          </Box>

          <Box sx={{ flex: 1, width: "100%" }}>
            <SimulationControls
              intensity={intensity}
              onIntensityChange={setIntensity}
              duration={duration}
              onDurationChange={setDuration}
            />
          </Box>

          <Box>
            <Button
              variant="contained"
              onClick={runSimulation}
              disabled={running}
            >
              {running ? "Running..." : "Run Simulation"}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {results.length > 0 && <SimulationResults results={results} />}
    </Container>
  );
}

// small helper to avoid extra import lines in top section
function PaperBox(props: React.ComponentProps<"div">) {
  return <Box component="div" {...props} />;
}
