import { Container, Typography, TextField, Button, Box } from "@mui/material";

export default function Contact() {
  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h3" gutterBottom>
        Contact Us
      </Typography>
      <Typography variant="body1" paragraph>
        Fill out the form below to get in touch!
      </Typography>
      <Box component="form" mt={3}>
        <TextField label="Name" fullWidth margin="normal" />
        <TextField label="Email" fullWidth margin="normal" />
        <TextField label="Message" fullWidth margin="normal" multiline rows={4} />
        <Button variant="contained" color="primary" sx={{ mt: 2 }}>
          Send
        </Button>
      </Box>
    </Container>
  );
}