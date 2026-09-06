import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import frFR from "antd/locale/fr_FR";
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={frFR}
      theme={{
        token: {
          colorPrimary: "#d85b36",
          colorPrimaryActive: "#8f351f",
          colorPrimaryHover: "#a94127",
          colorLink: "#d85b36",
          colorLinkActive: "#8f351f",
          colorLinkHover: "#a94127",
          borderRadius: 4,
          fontFamily: 'Inter, "Helvetica Neue", Arial, sans-serif',
        },
      }}
    >
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ConfigProvider>
  </React.StrictMode>,
);
