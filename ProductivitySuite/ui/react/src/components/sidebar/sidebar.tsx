// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from "react"
import { Tooltip, UnstyledButton, Stack, rem } from "@mantine/core"
import { IconHome2, IconLogout } from "@tabler/icons-react"
import classes from "./sidebar.module.scss"
import OpeaLogo from "../../assets/opea-icon-color.svg"
import { useAppDispatch } from "../../redux/store"
import { removeUser } from "../../redux/User/userSlice"
import { logout } from "../../redux/Conversation/ConversationSlice"
import { useNavigate } from "react-router-dom"
import { clearPrompts } from "../../redux/Prompt/PromptSlice"
import { useKeycloak } from "@react-keycloak/web"

interface NavbarLinkProps {
  icon: typeof IconHome2
  label: string
  path?: string
  active?: boolean
  onClick?(): void
}

function NavbarLink({ icon: Icon, label, active,path , onClick }: NavbarLinkProps) {
  const navigate = useNavigate();

  return (
    <Tooltip label={label} position="right" transitionProps={{ duration: 0 }}>
      <UnstyledButton onClick={()=> {onClick ? onClick() : navigate(path || "")}} className={classes.link} data-active={active || undefined}>
        <Icon style={{ width: rem(20), height: rem(20) }} stroke={1.5} />
        {/* <Text>{label}</Text> */}
      </UnstyledButton>
    </Tooltip>
  )
}

export interface SidebarNavItem {
  icon: typeof IconHome2
  label: string,
  path:string,
  children: React.ReactNode
}

export type SidebarNavList = SidebarNavItem[]

export interface SideNavbarProps {
  navList: SidebarNavList
}

export function SideNavbar({ navList }: SideNavbarProps) {
  const dispatch =useAppDispatch()
  const [active, setActive] = useState(0)
  const navigate = useNavigate();
  const {keycloak} = useKeycloak()


  const handleLogout = () => {
    dispatch(logout())
    dispatch(removeUser())
    dispatch(clearPrompts())
    keycloak.logout({})
  }

  const links = navList.map((link, index) => (
    <NavbarLink {...link} key={link.label} active={index === active} onClick={() => {
      setActive(index)
      navigate(link.path)
    }} />
  ))

  return (
    <nav className={classes.navbar}>
      <div className={classes.navbarLogo}>
        <img className={classes.logoImg} src={OpeaLogo} alt="opea logo" />
      </div>

      <div className={classes.navbarMain}>
        <Stack justify="center" gap={10}>
          {links}
        </Stack>
      </div>
      <Stack justify="center" gap={0}>
        <NavbarLink icon={IconLogout} label="Logout" onClick={handleLogout} />
      </Stack>
    </nav>
  )
}
