// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./App.scss"
import { MantineProvider } from "@mantine/core"
import '@mantine/notifications/styles.css';
import { SideNavbar, SidebarNavList } from "./components/sidebar/sidebar"
import { IconFileText } from "@tabler/icons-react"
import { Notifications } from '@mantine/notifications';
import DocSum from "./components/DocSum/DocSum";

const title = "Doc Summary"
const navList: SidebarNavList = [
  { icon: IconFileText, label: title }
]

function App() {
  
  return (
    <MantineProvider>
      <Notifications position="top-right" />
      <div className="layout-wrapper">
        <SideNavbar navList={navList} />
        <div className="content">
          <DocSum />
        </div>
      </div>
    </MantineProvider>
  )
}

export default App
