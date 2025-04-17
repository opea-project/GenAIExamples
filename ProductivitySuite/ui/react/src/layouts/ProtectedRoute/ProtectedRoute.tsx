import { useAppSelector } from "@redux/store";
import { userSelector } from "@redux/User/userSlice";
import React, { useEffect } from "react";

interface ProtectedRouteProps {
  component: React.ComponentType<any>;
  requiredRoles: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  component: Component,
  requiredRoles,
}) => {
  const { isAuthenticated, role } = useAppSelector(userSelector);

  const isAllowed = React.useMemo(() => {
    return isAuthenticated && requiredRoles.includes(role);
  }, [isAuthenticated, role, requiredRoles.join(",")]);

  if (!isAllowed) {
    return (
      <h1>Access Denied: You do not have permission to view this page.</h1>
    );
  }

  return <Component />;
};

export default ProtectedRoute;
