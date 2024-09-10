// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./App.scss"
import { MantineProvider } from "@mantine/core"
import '@mantine/notifications/styles.css';
import { SideNavbar, SidebarNavList } from "./components/sidebar/sidebar"
import { IconMessages } from "@tabler/icons-react"
import { Notifications } from '@mantine/notifications';
import CodeGen from "./components/CodeGen/CodeGen";

const title = "Code Gen"
const navList: SidebarNavList = [
  { icon: IconMessages, label: title }
]

function App() {
  
  return (
    <MantineProvider>
      <Notifications position="top-right" />
      <div className="layout-wrapper">
        <SideNavbar navList={navList} />
        <div className="content">
          <CodeGen  />
        </div>
      </div>
    </MantineProvider>
  )
}

export default App
