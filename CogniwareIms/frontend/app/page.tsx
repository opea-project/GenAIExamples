// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

"use client";

import React, { useState, useEffect } from "react";
import {
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Check,
  ChevronDown,
  MessageSquare,
  LogOut,
  User,
  Building,
  Package,
  FileText,
  BarChart3,
  Truck,
  Archive,
} from "lucide-react";

// Custom hook for typing effect
const useTypingEffect = (text: string, speed: number = 50) => {
  const [displayText, setDisplayText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayText((prev) => prev + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
      }, speed);
      return () => clearTimeout(timeout);
    }
  }, [currentIndex, text, speed]);

  return displayText;
};

// Logo Component - Using actual logo image with even larger sizes
const Logo = ({ size = "medium" }: { size?: "small" | "medium" | "large" }) => {
  const sizes = {
    small: "w-32 h-32",
    medium: "w-48 h-48",
    large: "w-64 h-64",
  };

  return (
    <div className={`${sizes[size]} flex items-center justify-center`}>
      <img
        src="/images/opea-stacked-logo-rwd.png"
        alt="OPEA Logo"
        className="w-full h-full object-contain"
      />
    </div>
  );
};

// Button with click effect
const variants = {
  primary:
    "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700",
  secondary: "bg-blue-600 hover:bg-blue-700",
  danger:
    "bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700",
  outline: "bg-white/5 border border-white/20 hover:bg-white/10",
  menu: "bg-white hover:bg-gray-50 border border-gray-200 text-black hover:text-black",
};

const AnimatedButton = ({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  className = "",
  ...props
}: {
  children: React.ReactNode;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  variant?: keyof typeof variants;
  className?: string;
  [key: string]: any;
}) => {
  const [ripples, setRipples] = useState<
    Array<{ x: number; y: number; id: number }>
  >([]);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const newRipple = { x, y, id: Date.now() };
    setRipples([...ripples, newRipple]);

    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
    }, 600);

    if (onClick && !disabled) {
      onClick(e);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={`relative overflow-hidden ${variants[variant]} ${className} transition-all duration-200 active:scale-95 ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
      {...props}
    >
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="absolute bg-white/30 rounded-full animate-ripple"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: "100px",
            height: "100px",
            transform: "translate(-50%, -50%)",
          }}
        />
      ))}
      {children}
    </button>
  );
};

// Sidebar Menu Component
const Sidebar = ({ currentUser }: { currentUser: string | null }) => {
  // Build an Agent section
  const buildAgentMenuItems = [
    { id: "features", label: "Platform Features", icon: MessageSquare },
    { id: "describe", label: "Describe Agent", icon: FileText },
    { id: "configure", label: "Configure Components", icon: Package },
    { id: "deploy", label: "Deploy Agent", icon: Truck },
  ];

  // Inventory Management section
  const inventoryMenuItems = [
    { id: "query", label: "Query Inventory", icon: MessageSquare },
    { id: "stock", label: "Stock Management", icon: Package },
    { id: "filter", label: "Product Filter", icon: FileText },
    { id: "allocations", label: "Allocations", icon: BarChart3 },
    { id: "warehouse", label: "Warehouse", icon: Building },
    { id: "assets", label: "Assets", icon: Archive },
    { id: "reports", label: "Reports", icon: Truck },
  ];

  const menuItems =
    currentUser === "Inventory Manager"
      ? inventoryMenuItems
      : buildAgentMenuItems;
  const sectionTitle =
    currentUser === "Inventory Manager"
      ? "Inventory Management"
      : "Build an Agent";

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 shadow-lg z-40 overflow-y-auto">
      {/* Logo in Sidebar */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12">
            <img
              src="/images/opea-stacked-logo-rwd.png"
              alt="OPEA Logo"
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <h2 className="font-bold text-black text-sm">AIPod Mini</h2>
            <p className="text-xs text-black">OPEA Platform</p>
          </div>
        </div>
      </div>

      {/* User Info */}
      {currentUser && (
        <div className="p-4 bg-blue-50 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <User size={16} className="text-blue-600" />
            <span className="text-sm font-medium text-black">
              {currentUser}
            </span>
          </div>
        </div>
      )}

      {/* Menu Items */}
      <nav className="p-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
          {sectionTitle}
        </h3>
        <div className="space-y-1">
          {menuItems.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer text-black group"
            >
              <item.icon
                size={20}
                className="text-gray-600 group-hover:text-blue-600"
              />
              <span className="text-sm font-medium group-hover:text-blue-600">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </nav>

      {/* Platform Info */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-gray-50">
        <div className="space-y-2">
          <div className="text-xs text-black">
            <strong>Version:</strong> 1.0.0
          </div>
          <div className="text-xs text-black">
            <strong>Environment:</strong> Production
          </div>
          <div className="text-xs text-black">
            <strong>Status:</strong>{" "}
            <span className="text-green-600">● Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Menu Component (kept for inventory pages)
const AdminMenu = ({
  currentPage,
  onPageChange,
}: {
  currentPage: string;
  onPageChange: (page: string) => void;
}) => {
  const menuItems = [
    { id: "query", label: "Query Inventory", icon: MessageSquare },
    { id: "stock", label: "Stock Management", icon: Package },
    { id: "filter", label: "Product Filter", icon: FileText },
    { id: "allocations", label: "Allocations", icon: BarChart3 },
    { id: "warehouse", label: "Warehouse", icon: Building },
    { id: "assets", label: "Assets", icon: Archive },
    { id: "reports", label: "Reports", icon: Truck },
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-lg mb-6">
      <h3 className="text-lg font-semibold text-black mb-4">
        Inventory Management
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {menuItems.map((item) => (
          <AnimatedButton
            key={item.id}
            onClick={() => onPageChange(item.id)}
            variant={currentPage === item.id ? "secondary" : "menu"}
            className={`p-3 rounded-lg flex flex-col items-center gap-2 text-sm font-medium ${
              currentPage === item.id ? "text-black" : "text-black"
            }`}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </AnimatedButton>
        ))}
      </div>
    </div>
  );
};

export default function OpeaAiAgentDemo() {
  const [currentStep, setCurrentStep] = useState(0);
  const [currentUser, setCurrentUser] = useState<string | null>(null);

  const steps = [
    { id: 0, title: "Welcome Screen" },
    { id: 1, title: "Platform Features" },
    { id: 2, title: "Consumer Role Login" },
    { id: 3, title: "Consumer Capabilities" },
    { id: 4, title: "Build AI Agent" },
    { id: 5, title: "Agent Configuration" },
    { id: 6, title: "Deployment Workflow" },
    { id: 7, title: "Logout Consumer" },
    { id: 8, title: "Inventory Manager Login" },
    { id: 9, title: "Query Inventory" },
    { id: 10, title: "Stock Management" },
    { id: 11, title: "Product Category Filter" },
    { id: 12, title: "Allocations Screen" },
    { id: 13, title: "Warehouse Management" },
    { id: 14, title: "Assets Management" },
    { id: 15, title: "Reports Dashboard" },
    { id: 16, title: "Final Screen" },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      // Add transition effect
      setTimeout(() => {
        setCurrentStep((prev) => prev + 1);
        window.scrollTo({ top: 0, behavior: "smooth" });
      }, 150);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      // Add transition effect
      setTimeout(() => {
        setCurrentStep((prev) => prev - 1);
        window.scrollTo({ top: 0, behavior: "smooth" });
      }, 150);
    }
  };

  const handleReset = () => {
    setCurrentStep(0);
    setCurrentUser(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <WelcomeScreen onNext={handleNext} />;
      case 1:
        return <PlatformFeatures onNext={handleNext} />;
      case 2:
        return (
          <LoginScreen
            role="Consumer"
            onLogin={() => setCurrentUser("Consumer")}
            onNext={handleNext}
          />
        );
      case 3:
        return <ConsumerCapabilities onNext={handleNext} />;
      case 4:
        return <BuildAIAgent onNext={handleNext} />;
      case 5:
        return <AgentConfiguration onNext={handleNext} />;
      case 6:
        return <DeploymentWorkflow onNext={handleNext} />;
      case 7:
        return (
          <LogoutScreen
            onLogout={() => setCurrentUser(null)}
            onNext={handleNext}
          />
        );
      case 8:
        return (
          <LoginScreen
            role="Inventory Manager"
            onLogin={() => setCurrentUser("Inventory Manager")}
            onNext={handleNext}
          />
        );
      case 9:
        return <QueryInventory onNext={handleNext} />;
      case 10:
        return <StockManagement onNext={handleNext} />;
      case 11:
        return <ProductCategoryFilter onNext={handleNext} />;
      case 12:
        return <AllocationsScreen onNext={handleNext} />;
      case 13:
        return <WarehouseManagement onNext={handleNext} />;
      case 14:
        return <AssetsManagement onNext={handleNext} />;
      case 15:
        return <ReportsDashboard onNext={handleNext} />;
      case 16:
        return <FinalScreen onReset={handleReset} />;
      default:
        return <WelcomeScreen onNext={handleNext} />;
    }
  };

  // Steps where sidebar should NOT be shown: Welcome, Login screens, Logout
  const hideSidebarSteps = [0, 2, 7, 8];
  const showSidebar = !hideSidebarSteps.includes(currentStep);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      {/* Sidebar - Hide on Welcome, Login, and Logout screens */}
      {showSidebar && <Sidebar currentUser={currentUser} />}

      {/* Main Content */}
      <div className={`py-12 px-6 ${showSidebar ? "ml-64" : ""}`}>
        {renderStep()}
      </div>
    </div>
  );
}

// Step Components
function WelcomeScreen({ onNext }: { onNext: () => void }) {
  return (
    <div className="max-w-6xl mx-auto px-6">
      <div className="text-center space-y-8 animate-fadeIn">
        {/* Logo */}
        <div className="flex justify-center">
          <Logo size="large" />
        </div>

        <h1 className="text-5xl font-bold text-black">
          Welcome to AIPod Mini OPEA Agent
        </h1>

        <p className="text-xl text-black max-w-3xl mx-auto">
          AI-powered inventory management system with specialized agents for
          every role
        </p>

        <p className="text-lg text-black max-w-2xl mx-auto">
          AIPod Mini powered system with specialized AI agents for every role
        </p>

        {/* Key Metrics */}
        <div className="flex justify-center gap-8 pt-8">
          <div className="flex items-center gap-3 px-6 py-3 bg-white rounded-xl shadow-sm border border-gray-200">
            <Building className="text-black" size={24} />
            <div>
              <div className="text-2xl font-bold text-black">12</div>
              <div className="text-black text-sm">AI Agents</div>
            </div>
          </div>
          <div className="flex items-center gap-3 px-6 py-3 bg-white rounded-xl shadow-sm border border-gray-200">
            <Package className="text-black" size={24} />
            <div>
              <div className="text-2xl font-bold text-black">287</div>
              <div className="text-black text-sm">Product Categories</div>
            </div>
          </div>
          <div className="flex items-center gap-3 px-6 py-3 bg-white rounded-xl shadow-sm border border-gray-200">
            <BarChart3 className="text-black" size={24} />
            <div>
              <div className="text-2xl font-bold text-black">Real-Time</div>
              <div className="text-black text-sm">Analytics</div>
            </div>
          </div>
        </div>

        {/* Role Selection */}
        <div className="pt-12">
          <h2 className="text-3xl font-bold text-black mb-8">
            Select Your Role
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {/* Consumer Role */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <User className="text-black" size={24} />
                </div>
                <h3 className="text-xl font-bold text-black">Consumer</h3>
              </div>
              <p className="text-black mb-4">
                Research Intel products, build PCs, and get AI recommendations.
              </p>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Product Search
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Build AI Appliance
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  AI Chat
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Product Comparison
                </li>
              </ul>
              <AnimatedButton
                onClick={onNext}
                variant="primary"
                className="w-full py-3 text-black rounded-lg"
              >
                Access Consumer →
              </AnimatedButton>
            </div>

            {/* Inventory Manager Role */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Building className="text-black" size={24} />
                </div>
                <h3 className="text-xl font-bold text-black">
                  Inventory Manager
                </h3>
              </div>
              <p className="text-black mb-4">
                Manage warehouse operations and track inventory with AI
                assistance.
              </p>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Stock Management
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Allocation
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Asset Tracking
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Reports
                </li>
              </ul>
              <AnimatedButton
                className="w-full py-3 bg-green-600 text-black"
                disabled
              >
                Coming Soon
              </AnimatedButton>
            </div>

            {/* Super Admin Role */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <FileText className="text-black" size={24} />
                </div>
                <h3 className="text-xl font-bold text-black">Super Admin</h3>
              </div>
              <p className="text-black mb-4">
                System administration and comprehensive analytics.
              </p>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  User Management
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  System Analytics
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Data Management
                </li>
                <li className="flex items-center gap-2 text-sm text-black">
                  <Check className="text-black" size={16} />
                  Configuration
                </li>
              </ul>
              <AnimatedButton
                className="w-full py-3 bg-purple-600 text-black"
                disabled
              >
                Coming Soon
              </AnimatedButton>
            </div>
          </div>
        </div>

        <div className="pt-8">
          <AnimatedButton
            onClick={onNext}
            variant="outline"
            className="mx-auto px-8 py-3 rounded-lg font-semibold flex items-center gap-2"
          >
            View Platform Features
            <ChevronDown size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function PlatformFeatures({ onNext }: { onNext: () => void }) {
  const features = [
    {
      icon: MessageSquare,
      title: "Interactive Agents",
      desc: "Build conversational AI agents",
    },
    {
      icon: FileText,
      title: "Document Processing",
      desc: "DocSummarization & DBQnA",
    },
    {
      icon: BarChart3,
      title: "Analytics & Insights",
      desc: "Real-time data analysis",
    },
    {
      icon: Truck,
      title: "Inventory Management",
      desc: "Complete warehouse solutions",
    },
    { icon: Archive, title: "Asset Tracking", desc: "Track and manage assets" },
    {
      icon: Building,
      title: "Multi-tenant",
      desc: "Role-based access control",
    },
  ];

  const handleClick = () => {
    console.log("Login as Consumer button clicked!");
    onNext();
  };

  return (
    <div className="max-w-7xl mx-auto px-6">
      <div className="text-center mb-12">
        <h2 className="text-5xl font-bold text-black mb-4">
          Platform Features
        </h2>
        <p className="text-xl text-black">
          Everything you need to build enterprise-grade AI applications
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {features.map((feature, idx) => (
          <div
            key={idx}
            className="p-6 bg-white rounded-xl border border-gray-200 hover:shadow-lg transition-all duration-300 animate-slideUp"
            style={{ animationDelay: `${idx * 100}ms` }}
          >
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg w-fit mb-4">
              <feature.icon size={32} className="text-white" />
            </div>
            <h3 className="text-xl font-bold text-black mb-2">
              {feature.title}
            </h3>
            <p className="text-black">{feature.desc}</p>
          </div>
        ))}
      </div>

      <div className="text-center pt-8 pb-12">
        <button
          onClick={handleClick}
          className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95 cursor-pointer inline-flex items-center gap-2"
        >
          Login as Consumer
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}

function LoginScreen({
  role,
  onLogin,
  onNext,
}: {
  role: string;
  onLogin: () => void;
  onNext: () => void;
}) {
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [showTyping, setShowTyping] = useState(false);

  const fullEmail =
    role === "Consumer" ? "consumer@company.com" : "inventory@company.com";
  const fullPassword = "password123";

  const typedEmail = useTypingEffect(fullEmail, 100);
  const typedPassword = useTypingEffect(fullPassword, 100);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowTyping(true);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const handleLogin = () => {
    setIsLoggingIn(true);
    setTimeout(() => {
      onLogin();
      setIsLoggingIn(false);
      onNext();
    }, 1200);
  };

  return (
    <div className="max-w-md mx-auto px-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-xl">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Logo size="large" />
          </div>
          <h2 className="text-3xl font-bold text-black mb-2">
            Login as {role}
          </h2>
          <p className="text-black">Secure authentication with OPEA Platform</p>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <div className="relative">
              <input
                type="email"
                value={showTyping ? typedEmail : ""}
                readOnly
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-black font-mono"
                placeholder="Typing..."
              />
              {showTyping && typedEmail.length < fullEmail.length && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-0.5 h-5 bg-blue-500 animate-pulse" />
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                value={
                  showTyping && typedEmail.length === fullEmail.length
                    ? typedPassword
                    : ""
                }
                readOnly
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-black font-mono"
                placeholder="Typing..."
              />
              {showTyping &&
                typedEmail.length === fullEmail.length &&
                typedPassword.length < fullPassword.length && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <div className="w-0.5 h-5 bg-blue-500 animate-pulse" />
                  </div>
                )}
            </div>
          </div>

          <AnimatedButton
            onClick={handleLogin}
            disabled={isLoggingIn || !showTyping}
            className="w-full py-3 text-black font-semibold flex items-center justify-center gap-2"
          >
            {isLoggingIn ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                Logging in...
              </>
            ) : (
              <>
                <Check size={20} />
                Login
              </>
            )}
          </AnimatedButton>
        </div>

        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-black text-sm text-center">
            <strong>Secure Access:</strong> Enterprise-grade authentication
            powered by OPEA
          </p>
        </div>
      </div>
    </div>
  );
}

function ConsumerCapabilities({ onNext }: { onNext: () => void }) {
  const capabilities = [
    "Browse product catalog and compare specifications",
    "Build custom PC configurations with AI assistance",
    "Get real-time pricing and availability",
    "Access technical documentation and guides",
    "Create and deploy custom AI agents",
    "Integrate with existing workflows",
  ];

  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Consumer Role Capabilities
        </h2>

        <div className="space-y-4">
          {capabilities.map((cap, idx) => (
            <div
              key={idx}
              className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-slideUp hover:shadow-sm transition-shadow"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <div className="p-2 bg-green-100 rounded-full">
                <Check size={20} className="text-black" />
              </div>
              <p className="text-lg text-black pt-1">{cap}</p>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            Build AI Agent
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function BuildAIAgent({ onNext }: { onNext: () => void }) {
  const [showTyping, setShowTyping] = useState(false);
  const fullText = "AI Agent for Inventory Management solution";
  const typedText = useTypingEffect(fullText, 80);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowTyping(true);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">Build AI Agent</h2>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe your AI Agent
            </label>
            <div className="relative">
              <textarea
                value={showTyping ? typedText : ""}
                readOnly
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-black h-32 resize-none font-mono"
                placeholder="Typing..."
              />
              {showTyping && typedText.length < fullText.length && (
                <div className="absolute right-3 top-3">
                  <div className="w-0.5 h-5 bg-blue-500 animate-pulse" />
                </div>
              )}
            </div>
            <p className="text-black text-sm mt-2">
              AI-powered agent creation with natural language processing
            </p>
          </div>

          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-black">
              <span className="font-semibold">✨ AI Analysis:</span> Based on
              your description, we recommend an Interactive Agent with Document
              Processing capabilities.
            </p>
          </div>

          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-black text-sm">
              <span className="font-semibold">Ready!</span> Your agent
              configuration is ready for deployment.
            </p>
          </div>

          <div className="text-center pt-4">
            <AnimatedButton
              onClick={onNext}
              variant="primary"
              className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
            >
              Configure Agent
              <ArrowRight size={20} />
            </AnimatedButton>
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentConfiguration({ onNext }: { onNext: () => void }) {
  const agents = [
    { name: "Interactive Agent", selected: true, required: true },
    { name: "DBQnA Agent", selected: true, required: false },
    { name: "DocSummarization Agent", selected: true, required: false },
    { name: "RAG Agent", selected: false, required: false },
    { name: "Audio Agent", selected: false, required: false },
  ];

  return (
    <div className="max-w-4xl mx-auto px-6">
      <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8">
        <h2 className="text-4xl font-bold text-black mb-6">
          Agent Configuration
        </h2>

        <p className="text-black mb-6">
          Components auto-selected for your Inventory Management Agent:
        </p>

        <div className="space-y-3 mb-8">
          {agents.map((agent, idx) => (
            <div
              key={idx}
              className={`flex items-center justify-between p-4 rounded-lg border transition-all ${
                agent.selected
                  ? "bg-green-500/20 border-green-500/50"
                  : "bg-white/5 border-white/20"
              }`}
            >
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={agent.selected}
                  readOnly
                  className="w-5 h-5 cursor-not-allowed"
                />
                <span className="text-black font-medium">{agent.name}</span>
                {agent.required && (
                  <span className="px-2 py-1 bg-purple-500/20 border border-purple-500/30 rounded text-xs text-black">
                    Required
                  </span>
                )}
                {agent.selected && !agent.required && (
                  <span className="px-2 py-1 bg-green-500/20 border border-green-500/30 rounded text-xs text-black">
                    Auto-selected
                  </span>
                )}
              </div>
              {agent.selected && <Check size={20} className="text-black" />}
            </div>
          ))}
        </div>

        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg mb-6">
          <p className="text-black text-sm">
            <span className="font-semibold">Configuration Ready!</span> DBQnA
            and DocSummarization agents have been automatically selected based
            on your requirements.
          </p>
        </div>

        <div className="text-center">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            Deploy Agent
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function DeploymentWorkflow({ onNext }: { onNext: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);

  const deploySteps = [
    { title: "Generating Code", duration: 2300, time: "2.3s" },
    { title: "Creating GitHub Repository", duration: 1800, time: "1.8s" },
    { title: "Building Container", duration: 4000, time: "45.2s" },
    { title: "Deploying to Cloud", duration: 3000, time: "12.7s" },
  ];

  useEffect(() => {
    if (currentStep < deploySteps.length) {
      const timer = setTimeout(() => {
        setCompletedSteps((prev) => [...prev, currentStep]);
        setCurrentStep((prev) => prev + 1);
      }, deploySteps[currentStep].duration);

      return () => clearTimeout(timer);
    } else if (currentStep === deploySteps.length && !showSuccess) {
      setTimeout(() => {
        setShowSuccess(true);
      }, 500);
    }
  }, [currentStep, deploySteps, showSuccess]);

  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Deployment Workflow
        </h2>

        <div className="space-y-4 mb-8">
          {deploySteps.map((step, idx) => {
            const isActive = idx === currentStep;
            const isCompleted = completedSteps.includes(idx);
            const progress = isActive ? 100 : 0;

            return (
              <div
                key={idx}
                className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                  isCompleted
                    ? "bg-green-50 border-green-500"
                    : isActive
                      ? "bg-blue-50 border-blue-500"
                      : "bg-gray-50 border-gray-200"
                }`}
              >
                <div className="flex items-center gap-4 mb-2">
                  <div
                    className={`p-2 rounded-full transition-all duration-300 ${
                      isCompleted
                        ? "bg-green-500"
                        : isActive
                          ? "bg-blue-500 animate-pulse"
                          : "bg-gray-300"
                    }`}
                  >
                    {isCompleted ? (
                      <Check size={20} className="text-white" />
                    ) : (
                      <div className="w-5 h-5 border-2 border-white rounded-full" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="text-black font-semibold">{step.title}</div>
                    <div className="text-sm text-black">
                      {isCompleted ? (
                        <span className="text-green-600">✓ Completed</span>
                      ) : isActive ? (
                        <span className="text-blue-600">⟳ Processing...</span>
                      ) : (
                        <span className="text-gray-500">Waiting...</span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-black font-mono">
                    {step.time}
                  </div>
                </div>

                {/* Progress Bar */}
                {isActive && (
                  <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300 ease-linear"
                      style={{
                        width: `${progress}%`,
                        animation: `loadProgress ${deploySteps[idx].duration}ms linear forwards`,
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {showSuccess && (
          <div className="p-6 bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-500 rounded-xl animate-slideUp">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-green-500 rounded-full">
                <Check size={24} className="text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-black mb-2">
                  🎉 Deployment Successful!
                </h3>
                <p className="text-black mb-4">
                  Inventory Management Agent created and deployed at:
                </p>
                <div className="p-3 bg-white rounded-lg font-mono text-sm text-black break-all mb-4 border border-gray-200">
                  https://inventory-agent-prod.azurewebsites.net
                </div>
                <div className="flex gap-3">
                  <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm transition-colors">
                    📁 View on GitHub
                  </button>
                  <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm transition-colors">
                    🚀 Open Agent
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showSuccess && (
          <>
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
              <p className="text-black text-sm">
                <span className="font-semibold">Next Step:</span> Logout from
                Consumer role and proceed to test the deployed agent as an
                Inventory Manager.
              </p>
            </div>

            <div className="text-center">
              <AnimatedButton
                onClick={onNext}
                variant="primary"
                className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
              >
                Continue to Logout
                <ArrowRight size={20} />
              </AnimatedButton>
            </div>
          </>
        )}
      </div>

      <style jsx>{`
        @keyframes loadProgress {
          from {
            width: 0%;
          }
          to {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

function LogoutScreen({
  onLogout,
  onNext,
}: {
  onLogout: () => void;
  onNext: () => void;
}) {
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = () => {
    setIsLoggingOut(true);
    setTimeout(() => {
      onLogout();
      setIsLoggingOut(false);
      onNext();
    }, 500);
  };

  return (
    <div className="max-w-md mx-auto px-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center shadow-lg">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-600 rounded-full flex items-center justify-center">
            <LogOut size={32} className="text-black" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-black mb-4">Logout</h2>
        <p className="text-black mb-8">
          Sign out of your current session securely
        </p>

        <AnimatedButton
          onClick={handleLogout}
          disabled={isLoggingOut}
          variant="danger"
          className="px-8 py-3 font-semibold flex items-center justify-center gap-2 mx-auto"
        >
          {isLoggingOut ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
              Logging out...
            </>
          ) : (
            <>
              <LogOut size={20} />
              Logout
            </>
          )}
        </AnimatedButton>
      </div>
    </div>
  );
}

function QueryInventory({ onNext }: { onNext: () => void }) {
  const [showTyping, setShowTyping] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [currentMenuPage, setCurrentMenuPage] = useState("query");
  const fullQuery =
    "Show inventory details for Xeon 6 processor at San Jose warehouse";
  const typedQuery = useTypingEffect(fullQuery, 50);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowTyping(true);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Show results only after typing is complete
  useEffect(() => {
    if (showTyping && typedQuery.length === fullQuery.length) {
      const timer = setTimeout(() => {
        setShowResults(true);
      }, 500); // Small delay after typing completes
      return () => clearTimeout(timer);
    }
  }, [showTyping, typedQuery.length, fullQuery.length]);

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Inventory Query Agent
        </h2>

        <div className="space-y-6">
          <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-lg">
            <div className="text-sm text-black mb-2 font-medium">
              User Query
            </div>
            <div className="relative">
              <div className="text-black font-mono text-lg min-h-[2rem]">
                {showTyping ? typedQuery : ""}
                {showTyping && typedQuery.length < fullQuery.length && (
                  <span className="w-0.5 h-5 bg-blue-500 animate-pulse inline-block ml-1" />
                )}
              </div>
            </div>
          </div>

          {showResults && (
            <div className="p-6 bg-gray-50 rounded-lg border border-gray-200 animate-slideUp">
              <div className="text-sm text-black mb-4 font-medium">
                Agent Response
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                    <div className="text-black text-sm mb-1">Product</div>
                    <div className="text-black font-semibold">
                      Intel Xeon 6 Processor
                    </div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                    <div className="text-black text-sm mb-1">SKU</div>
                    <div className="text-black font-semibold">CPU-XN6-2024</div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                    <div className="text-black text-sm mb-1">Location</div>
                    <div className="text-black font-semibold">
                      San Jose Warehouse
                    </div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                    <div className="text-black text-sm mb-1">
                      Available Stock
                    </div>
                    <div className="text-black font-semibold">247 units</div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                    <div className="text-black text-sm mb-1">Reserved</div>
                    <div className="text-black font-semibold">32 units</div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                    <div className="text-black text-sm mb-1">In Transit</div>
                    <div className="text-black font-semibold">15 units</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {showResults && (
          <div className="text-center mt-8">
            <AnimatedButton
              onClick={onNext}
              variant="primary"
              className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
            >
              View Stock Management
              <ArrowRight size={20} />
            </AnimatedButton>
          </div>
        )}
      </div>
    </div>
  );
}

function StockManagement({ onNext }: { onNext: () => void }) {
  const [currentMenuPage, setCurrentMenuPage] = useState("stock");
  const stockData = [
    {
      product: "Intel Xeon 6",
      sku: "CPU-XN6-2024",
      stock: 247,
      status: "In Stock",
      trend: "+12%",
    },
    {
      product: "AMD EPYC 9004",
      sku: "CPU-EP9-2024",
      stock: 189,
      status: "In Stock",
      trend: "+8%",
    },
    {
      product: "NVIDIA H100",
      sku: "GPU-H100-2024",
      stock: 45,
      status: "Low Stock",
      trend: "-15%",
    },
    {
      product: "Samsung DDR5 64GB",
      sku: "RAM-DD5-64",
      stock: 523,
      status: "In Stock",
      trend: "+23%",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">Stock Management</h2>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-black font-semibold">
                  Product
                </th>
                <th className="text-left py-3 px-4 text-black font-semibold">
                  SKU
                </th>
                <th className="text-left py-3 px-4 text-black font-semibold">
                  Stock
                </th>
                <th className="text-left py-3 px-4 text-black font-semibold">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-black font-semibold">
                  Trend
                </th>
              </tr>
            </thead>
            <tbody>
              {stockData.map((item, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <td className="py-4 px-4 text-black font-medium">
                    {item.product}
                  </td>
                  <td className="py-4 px-4 text-black font-mono text-sm">
                    {item.sku}
                  </td>
                  <td className="py-4 px-4 text-black font-semibold">
                    {item.stock}
                  </td>
                  <td className="py-4 px-4">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        item.status === "In Stock"
                          ? "bg-green-100 text-black"
                          : "bg-yellow-100 text-black"
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td
                    className={`py-4 px-4 font-semibold ${
                      item.trend.startsWith("+") ? "text-black" : "text-black"
                    }`}
                  >
                    {item.trend}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="text-center mt-8">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            View Product Filter
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function ProductCategoryFilter({ onNext }: { onNext: () => void }) {
  const [selectedCategory] = useState("Processors");
  const [selectedWarehouse] = useState("San Jose");
  const [currentMenuPage, setCurrentMenuPage] = useState("filter");

  const products = [
    {
      name: "Intel Xeon 6 5th Gen",
      warehouse: "San Jose",
      qty: 247,
      value: "$124,753",
    },
    {
      name: "Intel Xeon 6 6th Gen",
      warehouse: "San Jose",
      qty: 156,
      value: "$93,600",
    },
    {
      name: "AMD EPYC 9004 Series",
      warehouse: "San Jose",
      qty: 189,
      value: "$113,400",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Product Category Filter
        </h2>

        <div className="flex gap-4 mb-6">
          <div className="flex-1">
            <label className="block text-sm text-black mb-2 font-medium">
              Category
            </label>
            <select className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-black">
              <option>Processors</option>
              <option>Graphics Cards</option>
              <option>Memory</option>
              <option>Storage</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm text-black mb-2 font-medium">
              Warehouse
            </label>
            <select className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-black">
              <option>San Jose</option>
              <option>Austin</option>
              <option>Portland</option>
              <option>Denver</option>
            </select>
          </div>
        </div>

        <div className="space-y-3">
          {products.map((product, idx) => (
            <div
              key={idx}
              className="p-4 bg-gray-50 rounded-lg border border-gray-200 flex justify-between items-center hover:shadow-sm transition-shadow"
            >
              <div>
                <div className="text-black font-semibold">{product.name}</div>
                <div className="text-black text-sm">
                  {product.warehouse} Warehouse
                </div>
              </div>
              <div className="text-right">
                <div className="text-black font-semibold">
                  {product.qty} units
                </div>
                <div className="text-black text-sm">{product.value}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-8">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            View Allocations
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function AllocationsScreen({ onNext }: { onNext: () => void }) {
  const [currentMenuPage, setCurrentMenuPage] = useState("allocations");
  const allocations = [
    {
      id: "AL-2024-001",
      product: "Intel Xeon 6",
      customer: "Tech Corp",
      qty: 50,
      status: "Pending",
      date: "2024-10-10",
    },
    {
      id: "AL-2024-002",
      product: "NVIDIA H100",
      customer: "AI Solutions",
      qty: 20,
      status: "Confirmed",
      date: "2024-10-09",
    },
    {
      id: "AL-2024-003",
      product: "AMD EPYC 9004",
      customer: "Cloud Dynamics",
      qty: 35,
      status: "Shipped",
      date: "2024-10-08",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">Allocations</h2>

        <div className="space-y-4">
          {allocations.map((alloc, idx) => (
            <div
              key={idx}
              className="p-5 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-sm transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-black font-mono text-sm">{alloc.id}</div>
                  <div className="text-black font-semibold text-lg">
                    {alloc.product}
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    alloc.status === "Confirmed"
                      ? "bg-green-100 text-black"
                      : alloc.status === "Shipped"
                        ? "bg-blue-100 text-black"
                        : "bg-yellow-100 text-black"
                  }`}
                >
                  {alloc.status}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-black">Customer</div>
                  <div className="text-black font-medium">{alloc.customer}</div>
                </div>
                <div>
                  <div className="text-black">Quantity</div>
                  <div className="text-black font-medium">
                    {alloc.qty} units
                  </div>
                </div>
                <div>
                  <div className="text-black">Date</div>
                  <div className="text-black font-medium">{alloc.date}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-8">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            View Warehouse Management
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function WarehouseManagement({ onNext }: { onNext: () => void }) {
  const [currentMenuPage, setCurrentMenuPage] = useState("warehouse");
  const warehouses = [
    {
      name: "San Jose",
      capacity: "15,000 sq ft",
      utilization: "78%",
      items: 2847,
      temp: "68°F",
    },
    {
      name: "Austin",
      capacity: "12,000 sq ft",
      utilization: "65%",
      items: 1923,
      temp: "70°F",
    },
    {
      name: "Portland",
      capacity: "18,000 sq ft",
      utilization: "82%",
      items: 3456,
      temp: "66°F",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Warehouse Management
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {warehouses.map((warehouse, idx) => (
            <div
              key={idx}
              className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Building size={24} className="text-black" />
                </div>
                <h3 className="text-xl font-bold text-black">
                  {warehouse.name}
                </h3>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="text-black text-sm">Capacity</div>
                  <div className="text-black font-semibold">
                    {warehouse.capacity}
                  </div>
                </div>
                <div>
                  <div className="text-black text-sm">Utilization</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                        style={{ width: warehouse.utilization }}
                      />
                    </div>
                    <span className="text-black font-semibold">
                      {warehouse.utilization}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-black text-sm">Items</div>
                    <div className="text-black font-semibold">
                      {warehouse.items}
                    </div>
                  </div>
                  <div>
                    <div className="text-black text-sm">Temperature</div>
                    <div className="text-black font-semibold">
                      {warehouse.temp}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-8">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            View Assets Management
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function AssetsManagement({ onNext }: { onNext: () => void }) {
  const [currentMenuPage, setCurrentMenuPage] = useState("assets");
  const assets = [
    {
      id: "AST-2024-145",
      type: "Server Rack",
      location: "San Jose - A3",
      status: "Active",
      value: "$45,000",
    },
    {
      id: "AST-2024-146",
      type: "Forklift",
      location: "Austin - B2",
      status: "Active",
      value: "$32,000",
    },
    {
      id: "AST-2024-147",
      type: "Cooling System",
      location: "Portland - C1",
      status: "Maintenance",
      value: "$28,500",
    },
    {
      id: "AST-2024-148",
      type: "Security System",
      location: "San Jose - Main",
      status: "Active",
      value: "$18,900",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Assets Management
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {assets.map((asset, idx) => (
            <div
              key={idx}
              className="p-5 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-sm transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-black font-mono text-sm">{asset.id}</div>
                  <div className="text-black font-semibold text-lg">
                    {asset.type}
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    asset.status === "Active"
                      ? "bg-green-100 text-black"
                      : "bg-yellow-100 text-black"
                  }`}
                >
                  {asset.status}
                </span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-black">Location:</span>
                  <span className="text-black font-medium">
                    {asset.location}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-black">Value:</span>
                  <span className="text-black font-semibold">
                    {asset.value}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-8">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            View Reports Dashboard
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function ReportsDashboard({ onNext }: { onNext: () => void }) {
  const [currentMenuPage, setCurrentMenuPage] = useState("reports");

  return (
    <div className="max-w-6xl mx-auto px-6">
      <AdminMenu
        currentPage={currentMenuPage}
        onPageChange={setCurrentMenuPage}
      />

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
        <h2 className="text-4xl font-bold text-black mb-6">
          Reports Dashboard
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 bg-gradient-to-br from-green-50 to-blue-50 rounded-xl border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <BarChart3 size={24} className="text-black" />
              </div>
              <h3 className="text-xl font-bold text-black">
                Inventory Turnover
              </h3>
            </div>
            <div className="text-4xl font-bold text-black mb-2">4.2x</div>
            <div className="text-black text-sm">+12% vs last month</div>
          </div>

          <div className="p-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-purple-100 rounded-lg">
                <FileText size={24} className="text-black" />
              </div>
              <h3 className="text-xl font-bold text-black">
                Order Fulfillment
              </h3>
            </div>
            <div className="text-4xl font-bold text-black mb-2">96.8%</div>
            <div className="text-black text-sm">+3.2% vs last month</div>
          </div>

          <div className="p-6 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Truck size={24} className="text-black" />
              </div>
              <h3 className="text-xl font-bold text-black">
                Average Delivery Time
              </h3>
            </div>
            <div className="text-4xl font-bold text-black mb-2">2.4 days</div>
            <div className="text-black text-sm">-0.3 days vs last month</div>
          </div>

          <div className="p-6 bg-gradient-to-br from-orange-50 to-red-50 rounded-xl border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Archive size={24} className="text-orange-600" />
              </div>
              <h3 className="text-xl font-bold text-black">Stock Accuracy</h3>
            </div>
            <div className="text-4xl font-bold text-black mb-2">99.2%</div>
            <div className="text-black text-sm">+0.5% vs last month</div>
          </div>
        </div>

        <div className="text-center mt-8">
          <AnimatedButton
            onClick={onNext}
            variant="primary"
            className="px-8 py-4 rounded-lg font-semibold flex items-center gap-2 mx-auto"
          >
            Go to Dashboard
            <ArrowRight size={20} />
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}

function FinalScreen({ onReset }: { onReset: () => void }) {
  return (
    <div className="max-w-7xl mx-auto px-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-lg">
          <h1 className="text-4xl font-bold text-black mb-2">
            📊 Inventory Dashboard Overview
          </h1>
          <p className="text-black">
            Real-time inventory metrics and analytics powered by OPEA AI
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <Package size={32} className="text-blue-600" />
              <span className="text-green-600 text-sm font-semibold">+12%</span>
            </div>
            <div className="text-3xl font-bold text-black mb-1">2,847</div>
            <div className="text-sm text-black">Total Items</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <Building size={32} className="text-green-600" />
              <span className="text-green-600 text-sm font-semibold">
                3 Active
              </span>
            </div>
            <div className="text-3xl font-bold text-black mb-1">3</div>
            <div className="text-sm text-black">Warehouses</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <Truck size={32} className="text-purple-600" />
              <span className="text-blue-600 text-sm font-semibold">+8%</span>
            </div>
            <div className="text-3xl font-bold text-black mb-1">156</div>
            <div className="text-sm text-black">Active Allocations</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 size={32} className="text-orange-600" />
              <span className="text-green-600 text-sm font-semibold">
                99.2%
              </span>
            </div>
            <div className="text-3xl font-bold text-black mb-1">$2.4M</div>
            <div className="text-sm text-black">Inventory Value</div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stock Levels Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-xl font-bold text-black mb-4">
              Stock Levels by Category
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-black font-medium">
                    Processors (Xeon, EPYC)
                  </span>
                  <span className="text-black">436 units</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full"
                    style={{ width: "78%" }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-black font-medium">
                    GPUs (H100, A100)
                  </span>
                  <span className="text-black">45 units</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-purple-600 h-3 rounded-full"
                    style={{ width: "25%" }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-black font-medium">Memory (DDR5)</span>
                  <span className="text-black">523 units</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full"
                    style={{ width: "92%" }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-black font-medium">Storage (NVMe)</span>
                  <span className="text-black">312 units</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-orange-600 h-3 rounded-full"
                    style={{ width: "65%" }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Warehouse Utilization */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-xl font-bold text-black mb-4">
              Warehouse Utilization
            </h3>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-black font-medium">San Jose</span>
                  <span className="text-black font-semibold">78%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-cyan-500 h-4 rounded-full flex items-center justify-end pr-2"
                    style={{ width: "78%" }}
                  >
                    <span className="text-white text-xs font-bold">78%</span>
                  </div>
                </div>
                <div className="text-xs text-black mt-1">
                  2,847 items • 15,000 sq ft
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-black font-medium">Austin</span>
                  <span className="text-black font-semibold">65%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-4 rounded-full flex items-center justify-end pr-2"
                    style={{ width: "65%" }}
                  >
                    <span className="text-white text-xs font-bold">65%</span>
                  </div>
                </div>
                <div className="text-xs text-black mt-1">
                  1,923 items • 12,000 sq ft
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-black font-medium">Portland</span>
                  <span className="text-black font-semibold">82%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-red-500 h-4 rounded-full flex items-center justify-end pr-2"
                    style={{ width: "82%" }}
                  >
                    <span className="text-white text-xs font-bold">82%</span>
                  </div>
                </div>
                <div className="text-xs text-black mt-1">
                  3,456 items • 18,000 sq ft
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-xl font-bold text-black mb-4">
            Recent Inventory Activity
          </h3>
          <div className="space-y-3">
            <div className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <Package size={20} className="text-blue-600" />
              <div className="flex-1">
                <div className="text-sm font-semibold text-black">
                  Stock Updated: Intel Xeon 6
                </div>
                <div className="text-xs text-black">
                  San Jose Warehouse • +50 units
                </div>
              </div>
              <div className="text-xs text-black">2 mins ago</div>
            </div>

            <div className="flex items-center gap-4 p-3 bg-green-50 rounded-lg border border-green-100">
              <div className="w-2 h-2 bg-green-600 rounded-full"></div>
              <Truck size={20} className="text-green-600" />
              <div className="flex-1">
                <div className="text-sm font-semibold text-black">
                  Allocation Completed: AL-2024-003
                </div>
                <div className="text-xs text-black">
                  Cloud Dynamics • 35 units shipped
                </div>
              </div>
              <div className="text-xs text-black">15 mins ago</div>
            </div>

            <div className="flex items-center gap-4 p-3 bg-purple-50 rounded-lg border border-purple-100">
              <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
              <Building size={20} className="text-purple-600" />
              <div className="flex-1">
                <div className="text-sm font-semibold text-black">
                  Warehouse Alert: Portland at 82%
                </div>
                <div className="text-xs text-black">
                  Consider redistribution to optimize space
                </div>
              </div>
              <div className="text-xs text-black">1 hour ago</div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-black">
                Need to explore more?
              </h3>
              <p className="text-sm text-black">
                Restart the journey to experience different workflows
              </p>
            </div>
            <AnimatedButton
              onClick={onReset}
              variant="primary"
              className="px-6 py-3 rounded-lg font-semibold flex items-center gap-2"
            >
              <RotateCcw size={20} />
              Restart Experience
            </AnimatedButton>
          </div>
        </div>
      </div>
    </div>
  );
}
