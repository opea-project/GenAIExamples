import "./App.scss";

import React, { Suspense, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "@layouts/ProtectedRoute/ProtectedRoute";

import { useKeycloak } from "@react-keycloak/web";
import { setUser, userSelector } from "@redux/User/userSlice";

import MainLayout from "@layouts/Main/MainLayout";
import MinimalLayout from "@layouts/Minimal/MinimalLayout";
import Notification from "@components/Notification/Notification";
import { Box, styled, Typography } from "@mui/material";
import { AtomAnimation, AtomIcon } from "@icons/Atom";

import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  conversationSelector,
  getAllConversations,
  /*getStoredPromptSettings,*/ getSupportedModels,
  getSupportedUseCases,
} from "@redux/Conversation/ConversationSlice";
import { getPrompts } from "@redux/Prompt/PromptSlice";

import Home from "@pages/Home/Home";
import ChatView from "@pages/Chat/ChatView";

const HistoryView = React.lazy(() => import("@pages/History/HistoryView"));
const DataSourceManagement = React.lazy(
  () => import("@pages/DataSource/DataSourceManagement"),
);

const LoadingBox = styled(Box)({
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  height: "100vh",
  width: "100vw",
});

const App = () => {
  const { keycloak } = useKeycloak();
  const dispatch = useAppDispatch();

  const { name } = useAppSelector(userSelector);
  const { useCase } = useAppSelector(conversationSelector);

  useEffect(() => {
    //TODO: get role from keyCloack scope, defaulting to Admin
    dispatch(
      setUser({
        name: keycloak?.idTokenParsed?.preferred_username,
        isAuthenticated: true,
        role: "Admin",
      }),
    );
  }, [keycloak.idTokenParsed]);

  const initSettings = () => {
    if (keycloak.authenticated) {
      dispatch(getSupportedUseCases());
      dispatch(getSupportedModels());
      dispatch(getPrompts());
    }
  };

  useEffect(() => {
    if (keycloak.authenticated) initSettings();
  }, [keycloak.authenticated]);

  //TODO: on potential useCase change get different conversation data
  useEffect(() => {
    if (keycloak.authenticated && useCase) {
      dispatch(getAllConversations({ user: name, useCase: useCase }));
      // dispatch(getSharedConversations({ usecase: selectedUseCase.use_case }));
    }
  }, [useCase, name]);

  return !keycloak.authenticated ? (
    <LoadingBox>
      <AtomIcon />
      <Typography>redirecting to sso ...</Typography>
    </LoadingBox>
  ) : (
    <BrowserRouter>
      <Suspense
        fallback={
          <LoadingBox>
            <AtomIcon />
          </LoadingBox>
        }
      >
        <Routes>
          {/* Routes wrapped in MainLayout */}
          <Route element={<MainLayout />}>
            <Route
              path="/"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={Home}
                />
              }
            />
          </Route>

          <Route element={<MainLayout dataView={true} />}>
            <Route
              path="/data"
              element={
                <ProtectedRoute
                  requiredRoles={["Admin"]}
                  component={DataSourceManagement}
                />
              }
            />
          </Route>

          <Route element={<MainLayout historyView={true} />}>
            <Route
              path="/shared"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={(props) => (
                    <HistoryView {...props} shared={true} />
                  )}
                />
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={(props) => (
                    <HistoryView {...props} shared={false} />
                  )}
                />
              }
            />
          </Route>

          <Route element={<MainLayout chatView={true} />}>
            <Route
              path="/faq/:conversation_id"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={ChatView}
                />
              }
            />
            <Route
              path="/code/:conversation_id"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={ChatView}
                />
              }
            />
            <Route
              path="/chat/:conversation_id"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={ChatView}
                />
              }
            />
            <Route
              path="/summary/:conversation_id"
              element={
                <ProtectedRoute
                  requiredRoles={["User", "Admin"]}
                  component={ChatView}
                />
              }
            />
          </Route>

          {/* Routes not wrapped in MainLayout */}
          <Route element={<MinimalLayout />}>
            {/* <Route path="/xxxx" element={<xxxx />} /> */}
          </Route>
        </Routes>
        <Notification />
      </Suspense>
    </BrowserRouter>
  );
};

export default App;
