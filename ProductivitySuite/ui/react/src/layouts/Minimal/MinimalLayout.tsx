// About pages or privacy policy are likely minimal layouts
import { Outlet } from "react-router-dom";
import styles from "./MinimalLayout.module.scss";

const MinimalLayout = () => {
  return (
    <div className={styles.minimalLayout}>
      <Outlet />
    </div>
  );
};

export default MinimalLayout;
