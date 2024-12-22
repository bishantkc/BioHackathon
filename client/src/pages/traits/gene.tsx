import { useEffect, useState } from "react";
import {
  Container,
  Grid,
  TextField,
  Button,
  Typography,
  Paper,
  Box,
  ThemeProvider,
  createTheme,
  Alert,
} from "@mui/material";
import axiosInstance from "../../utils/axios";
import Sidebar from "../../components/Sidebar/sidebar";
import Navbar from "../../components/Navbar/navbar";
import { LoadingPage } from "../../utils/pageLoading";
import "ldrs/dotSpinner";

const defaultTheme = createTheme();

const GeneInfoApp = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [geneInfo, setGeneInfo] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchTerm?.trim()) {
      setLoading(false);
      setError("Please fill in the field");
      return;
    }

    setError("");
    setGeneInfo(null);
    setLoading(true);

    try {
      const response = await axiosInstance.get(`/get_genes_info`, {
        params: { gene_name: searchTerm },
      });
      setGeneInfo(response?.data);
    } catch (err: any) {
      setError("Incorrect gene name. Please retry with a valid name.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError("");
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <ThemeProvider theme={defaultTheme}>
      <div>
        {/* Sidebar Component */}
        <Sidebar />

        {/* Main Content */}
        <div className="home">
          {/* Navbar Component */}
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
                label="Search Gene"
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
              {/* Gene Info Section */}
              <Grid item xs={12} md={6}>
                <Typography variant="h5" gutterBottom>
                  Gene Information
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
                  ) : geneInfo ? (
                    <>
                      <Typography variant="body1" gutterBottom>
                        <strong>Gene ID:</strong> {geneInfo.gene_id}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Gene Name:</strong> {geneInfo.gene_name}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Official Full Name:</strong>{" "}
                        {geneInfo.official_full_name}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Summary:</strong> {geneInfo.summary}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Location:</strong> {geneInfo.location}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Lineage:</strong> {geneInfo.lineage}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        <strong>Aliases:</strong>{" "}
                        {geneInfo.aliases?.join(", ") || "None"}
                      </Typography>
                    </>
                  ) : (
                    <Typography variant="body1" color="textSecondary">
                      Search for a gene to view its information.
                    </Typography>
                  )}
                </Paper>
              </Grid>

              {/* Genomic Sequence Section */}
              <Grid item xs={12} md={6}>
                <Typography variant="h5" gutterBottom>
                  Genomic Sequence
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
                  ) : geneInfo?.sequence ? (
                    <Typography
                      variant="body2"
                      sx={{
                        wordBreak: "break-word",
                        whiteSpace: "pre-wrap",
                        fontFamily: "monospace",
                      }}
                    >
                      {geneInfo.sequence}
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

export default GeneInfoApp;
