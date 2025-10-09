import { Container, Typography, Card, CardContent, CardMedia, Box } from "@mui/material";

export default function About() {
  return (
    <Container maxWidth="md" sx={{ mt: 5 }}>
      <Typography variant="h3" gutterBottom>
        About Us
      </Typography>

      <Card sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, mt: 3 }}>
        <CardMedia
          component="img"
          sx={{ width: { xs: "100%", md: 300 }, height: "auto" }}
          image="https://source.unsplash.com/600x400/?team,work"
          alt="Our team"
        />

        <Box sx={{ display: "flex", flexDirection: "column" }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Who We Are
            </Typography>
            <Typography variant="body1" paragraph>
              We are a passionate team dedicated to building modern, user-friendly
              web applications. Our mission is to deliver clean, efficient, and
              scalable solutions for businesses and individuals.
            </Typography>
            <Typography variant="body1">
              This project demonstrates how React, React Router, and Material UI
              can work together to create beautiful and functional web apps.
            </Typography>
          </CardContent>
        </Box>
      </Card>
    </Container>
  );
}
