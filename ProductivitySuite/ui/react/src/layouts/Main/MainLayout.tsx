import Header from "@components/Header/Header";
import { SideBarSpacer } from "@components/SideBar/SideBar";
import { useState } from "react";
import { Outlet } from "react-router-dom";
import styles from "./MainLayout.module.scss";

interface MainLayoutProps {
  chatView?: boolean;
  historyView?: boolean;
  dataView?: boolean;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  chatView = false,
  historyView = false,
  dataView = false,
}) => {
  const [asideOpen, setAsideOpen] = useState(false);

  return (
    <div className={styles.mainLayout}>
      <Header
        setAsideOpen={setAsideOpen}
        asideOpen={asideOpen}
        chatView={chatView}
        historyView={historyView}
        dataView={dataView}
      />
      <div className={styles.mainWrapper}>
        <SideBarSpacer asideOpen={asideOpen} />
        <div className={styles.contentWrapper}>
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default MainLayout;
