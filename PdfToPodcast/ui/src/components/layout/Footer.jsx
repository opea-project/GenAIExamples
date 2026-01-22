export const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <span className="text-base text-gray-700 font-medium">Powered by</span>
            <div className="flex items-center gap-2">
              {/* Cloud2Labs Logo - Replace src with your actual logo */}
              <img
                src="/cloud2labs-logo.png"
                alt="Cloud2Labs"
                className="h-12 w-auto"
                onError={(e) => {
                  // Fallback to text if image not found
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <span
                className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent hidden"
                style={{ display: 'none' }}
              >
                Cloud2Labs
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
            >
              Documentation
            </a>
            <a
              href="/privacy"
              className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
            >
              Privacy
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
