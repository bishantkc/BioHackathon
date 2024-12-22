import { useEffect, useState } from "react";
import {
  Container,
  Grid,
  TextField,
  Button,
  Typography,
  Paper,
  Box,
  createTheme,
  ThemeProvider,
  Alert,
} from "@mui/material";
import axiosInstance from "../../utils/axios";
import Sidebar from "../../components/Sidebar/sidebar";
import Navbar from "../../components/Navbar/navbar";
import { LoadingPage } from "../../utils/pageLoading";

const defaultTheme = createTheme();

const ProteinInfoApp = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [proteinInfo, setProteinInfo] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchTerm?.trim()) {
      setLoading(false);
      setError("Please fill in the field");
      return;
    }

    setError("");
    setProteinInfo(null);
    setLoading(true);

    try {
      const response = await axiosInstance.get(`/get_protein_info`, {
        params: { protein_name: searchTerm },
      });

      console.log(response);
      setProteinInfo(response?.data);
    } catch (err: any) {
      setError("Incorrect protein name. Please retry with a valid name.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError("");
      }, 3000);

      return () => clearTimeout(timer); // Cleanup timeout
    }
  }, [error]);

  return (
    <ThemeProvider theme={defaultTheme}>
      <div>
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <div className="home">
          {/* Navbar */}
          <Navbar />
          <LoadingPage />

          <Container maxWidth="lg" sx={{ mt: 4 }}>
            {/* Search Bar */}
            <Box
              display="flex"
              justifyContent="center"
              alignItems="center"
              gap={2}
              mb={4}
            >
              <TextField
                label="Search Protein"
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                sx={{
                  width: "50%",
                  maxWidth: "600px",
                  backgroundColor: "#fff",
                  borderRadius: 2,
                  boxShadow: 2,
                }}
              />
              {error && (
                <Alert
                  severity="error"
                  onClose={() => setError("")}
                  style={{
                    position: "fixed",
                    top: "20px",
                    marginRight: "100px",
                  }}
                >
                  {error}
                </Alert>
              )}
              <Button
                variant="contained"
                color="primary"
                onClick={handleSearch}
                sx={{
                  paddingX: 3,
                  borderRadius: 2,
                  boxShadow: 2,
                  "&:hover": {
                    backgroundColor: "#4e94d1",
                  },
                }}
              >
                Search
              </Button>
            </Box>

            <Grid container spacing={4}>
              {/* Protein Info Section */}
              <Grid item xs={12} md={6}>
                <Typography variant="h5" gutterBottom>
                  Protein Information
                </Typography>
                <Paper
                  sx={{
                    p: 3,
                    borderRadius: 2,
                    maxHeight: 500,
                    overflow: "auto",
                    boxShadow: 3,
                  }}
                >
                  {loading ? (
                    <Box
                      display="flex"
                      justifyContent="center"
                      alignItems="center"
                      minHeight="150px"
                    >
                      <l-dot-spinner
                        size="50"
                        speed="0.9"
                        color="#2abf2d"
                      ></l-dot-spinner>
                    </Box>
                  ) : proteinInfo ? (
                    <>
                      <Typography variant="body1" gutterBottom>
                        <strong>Protein ID:</strong> {proteinInfo.protein_id}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Definition:</strong> {proteinInfo.definition}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Length:</strong> {proteinInfo.length}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Accession:</strong> {proteinInfo.accession}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Source:</strong> {proteinInfo.source}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Organism:</strong> {proteinInfo.organism}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Comment:</strong> {proteinInfo.comment}
                      </Typography>
                    </>
                  ) : (
                    <Typography variant="body1" color="textSecondary">
                      Search for a protein to view its information.
                    </Typography>
                  )}
                </Paper>
              </Grid>

              {/* Sequence Section */}
              <Grid item xs={12} md={6}>
                <Typography variant="h5" gutterBottom>
                  Protein Sequence
                </Typography>
                <Paper
                  sx={{
                    p: 3,
                    overflow: "auto",
                    maxHeight: 500,
                    borderRadius: 2,
                    boxShadow: 3,
                  }}
                >
                  {loading ? (
                    <Box
                      display="flex"
                      justifyContent="center"
                      alignItems="center"
                      minHeight="150px"
                    >
                      <l-dot-spinner
                        size="50"
                        speed="0.9"
                        color="#2abf2d"
                      ></l-dot-spinner>
                    </Box>
                  ) : proteinInfo?.sequence ? (
                    <Typography
                      variant="body2"
                      sx={{
                        wordBreak: "break-word",
                        whiteSpace: "pre-wrap",
                        fontFamily: "monospace",
                      }}
                    >
                      {proteinInfo.sequence}
                    </Typography>
                  ) : (
                    <Typography variant="body1" color="textSecondary">
                      Sequence will be displayed here upon search.
                    </Typography>
                  )}
                </Paper>
              </Grid>
            </Grid>
          </Container>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default ProteinInfoApp;
