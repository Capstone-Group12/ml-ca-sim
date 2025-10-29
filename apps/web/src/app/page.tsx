import { Container, Typography, Button, Box } from "@mui/material";
import Link from "next/link";

export default function Home() {
  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h3" gutterBottom>
        Welcome to My Website
      </Typography>
      <Typography variant="body1" paragraph>
        This is the home page built with Material UI. You can navigate to other
        pages using the navbar above.
      </Typography>

      <Box mt={3}>
        <Button
          variant="contained"
          color="primary"
          component={Link}
          href="/contact"
        >
          Contact Us
        </Button>
      </Box>
    </Container>
  );
}
