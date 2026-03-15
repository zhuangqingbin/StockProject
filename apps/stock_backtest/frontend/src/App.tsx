import { Suspense } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";

import { TopNavigation } from "./components/TopNavigation";
import { appRoutes } from "./lib/routeModules";
import "./styles/app.css";

const queryClient = new QueryClient();

const RouteDeckFallback = () => (
  <div className="route-fallback" role="status">
    <div className="route-fallback__line route-fallback__line--title" />
    <div className="route-fallback__line" />
    <div className="route-fallback__line route-fallback__line--short" />
  </div>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <div className="app-shell">
      <div className="app-shell__texture" aria-hidden="true" />
      <div className="app-shell__inner">
        <TopNavigation />
        <main className="page-frame">
          <Suspense fallback={<RouteDeckFallback />}>
            <Routes>
              <Route element={<Navigate replace to="/dashboard" />} path="/" />
              {appRoutes.map((route) => (
                <Route element={<route.component />} key={route.path} path={route.path} />
              ))}
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  </QueryClientProvider>
);

export default App;
