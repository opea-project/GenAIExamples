// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./App.scss"
import {MantineProvider } from "@mantine/core"
import '@mantine/notifications/styles.css';
import { SideNavbar, SidebarNavList } from "./components/sidebar/sidebar"
import { IconMessages, IconFileTextAi, IconCode, IconFileInfo, IconDatabaseCog } from "@tabler/icons-react"
import Conversation from "./components/Conversation/Conversation"
import { Notifications } from '@mantine/notifications';
import { BrowserRouter, Route, Routes } from "react-router-dom";
import CodeGen from "./components/CodeGen/CodeGen";
import DocSum from "./components/DocSum/DocSum";
import FaqGen from "./components/FaqGen/FaqGen";
import { useKeycloak } from "@react-keycloak/web";
import DataSource from "./components/Conversation/DataSource";
import { useAppDispatch } from "./redux/store";
import { setUser } from "./redux/User/userSlice";
import { useEffect } from "react";

const title = "Chat QnA"
const navList: SidebarNavList = [
  { icon: IconMessages, label: "Chat Qna", path: "/", children: <Conversation title={title} /> },
  { icon: IconCode, label: "CodeGen", path: "/codegen", children: <CodeGen /> },
  { icon: IconFileTextAi, label: "DocSum", path: "/docsum", children: <DocSum /> },
  { icon: IconFileInfo, label: "FaqGen", path: "/faqgen", children: <FaqGen /> },
  { icon: IconDatabaseCog, label: "Data Management", path: "/data-management", children: <DataSource /> }
]

function App() {
  const { keycloak } = useKeycloak();
  const dispatch = useAppDispatch()
  useEffect(()=>{
    dispatch(setUser(keycloak?.idTokenParsed?.preferred_username))
  },[keycloak.idTokenParsed])
  
  return (
    <>
      <MantineProvider>
      {!keycloak.authenticated ? (
        "redirecting to sso ..."
      ) : (
        <BrowserRouter>
          
            <Notifications position="top-right" />
            <div className="layout-wrapper">
              <SideNavbar navList={navList} />
              <div className="content">
                <Routes>
                  {navList.map(tab => {
                    return (<Route path={tab.path} element={tab.children} />)
                  })}

                </Routes>

                <Conversation title={title} />
              </div>
            </div>
        </BrowserRouter>
      )}
      </MantineProvider>

    </>
  )

}

export default App
