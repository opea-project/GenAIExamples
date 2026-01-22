export const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 py-6 mt-12">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="flex items-center space-x-2">
            <img
              src="/cloud2labs-logo.png"
              alt="Cloud2Labs"
              className="h-8 object-contain"
            />
            <span className="text-sm font-medium text-gray-700">Cloud2Labs</span>
          </div>
          <p className="text-xs text-gray-500">
            © 2025 Cloud2Labs. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
