import "./App.scss";
import { MantineProvider } from "@mantine/core";
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { SideNavbar, SidebarNavList } from "./components/sidebar/sidebar";
import { IconFileText } from "@tabler/icons-react";
import { Notifications } from '@mantine/notifications';
import DBConnect from "./components/DbConnect/DBConnect";

const title = "DBQnA";
const navList: SidebarNavList = [
  { icon: IconFileText, label: title },
];


function App() {
  return (
    <MantineProvider >
      <Notifications position="top-right" />
      <div className="layout-wrapper">
        <SideNavbar navList={navList} />
        <div className="content">
          <DBConnect />
        </div>
      </div>
    </MantineProvider>
  );
}

export default App;
