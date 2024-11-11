// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./App.scss"
import { MantineProvider } from "@mantine/core"
import '@mantine/notifications/styles.css';
import { SideNavbar, SidebarNavList } from "./components/sidebar/sidebar"
import { IconMessages } from "@tabler/icons-react"
import UserInfoModal from "./components/UserInfoModal/UserInfoModal"
import Conversation from "./components/Conversation/Conversation"
import { Notifications } from '@mantine/notifications';

const title = "Chat QnA"
const navList: SidebarNavList = [
  { icon: IconMessages, label: title }
]

function App() {
  
  return (
    <MantineProvider>
      <Notifications position="top-right" />
      <UserInfoModal />
      <div className="layout-wrapper">
        <SideNavbar navList={navList} />
        <div className="content">
          <Conversation title={title} />
        </div>
      </div>
    </MantineProvider>
  )
}

export default App
