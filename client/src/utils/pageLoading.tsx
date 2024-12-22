import { LinearProgress } from "@mui/material";
import { useEffect, useState } from "react";

export const LoadingPage = () => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setIsLoading(false);
    }, 2000); // Simulating a 2-second delay
  }, []);

  return (
    <div style={{ width: "100%" }}>
      {isLoading && (
        <div style={{ width: "100%" }}>
          <LinearProgress color="success" />
        </div>
      )}
    </div>
  );
};
