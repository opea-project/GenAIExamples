export interface User {
  name: string;
  isAuthenticated: boolean;
  role: "Admin" | "User";
}
