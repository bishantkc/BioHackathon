import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./App.css";
import GeneInfoApp from "./pages/traits/gene";
import ProteinInfoApp from "./pages/traits/protein";

function App() {
  const router = createBrowserRouter([
    {
      path: "/gene",
      element: <GeneInfoApp />,
    },
    {
      path: "/protein",
      element: <ProteinInfoApp />,
    },
  ]);

  return <RouterProvider router={router} />;
}

export default App;
