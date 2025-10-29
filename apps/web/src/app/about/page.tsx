import { Container, Typography } from "@mui/material";

export default function About() {
  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h3" gutterBottom>
        About Us
      </Typography>
      <Typography variant="body1" paragraph>
        This is the About page. Here you can learn more about our website and team.
      </Typography>
    </Container>
  );
}