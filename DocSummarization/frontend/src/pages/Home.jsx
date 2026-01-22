import { Link } from 'react-router-dom';
import { FileText, ArrowRight, Sparkles, Zap, Settings } from 'lucide-react';

export const Home = () => {
  const features = [
    {
      icon: FileText,
      title: 'Multiple Input Formats',
      description: 'Supports text, PDF, and DOC/DOCX document files',
    },
    {
      icon: Sparkles,
      title: 'AI-Powered Summarization',
      description: 'Advanced AI creates concise, accurate summaries of your content',
    },
    {
      icon: Settings,
      title: 'Smart Processing',
      description: 'Automatically optimizes summarization for your content type',
    },
    {
      icon: Zap,
      title: 'Fast & Efficient',
      description: 'Get instant summaries with real-time streaming support',
    },
  ];

  const steps = [
    {
      number: 1,
      title: 'Choose Input Type',
      description: 'Select from text or document upload',
    },
    {
      number: 2,
      title: 'Upload or Paste',
      description: 'Upload your file or paste text content',
    },
    {
      number: 3,
      title: 'Get Summary',
      description: 'Receive your AI-generated summary instantly',
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-6 py-12">
        <div className="inline-block">
          <img
            src="/cloud2labs-logo.png"
            alt="Cloud2Labs"
            className="w-32 h-32 object-contain mx-auto mb-6"
          />
        </div>

        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
          Intelligent Document
          <br />
          <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
            Summarization
          </span>
        </h1>

        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Transform any text or document into concise, meaningful summaries
          powered by advanced AI. Perfect for research, content analysis, and information extraction.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
          <Link to="/generate">
            <button className="btn-primary flex items-center gap-2 px-8 py-3 text-lg">
              Get Started
              <ArrowRight className="w-5 h-5" />
            </button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section>
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Why Choose Document Summarization?
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="bg-primary-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section>
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-secondary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-4 shadow-lg">
                  {step.number}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-gray-600">{step.description}</p>
              </div>
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-8 left-1/2 w-full h-0.5 bg-gradient-to-r from-primary-600 to-secondary-600 opacity-30" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-12 text-center text-white shadow-xl">
        <h2 className="text-3xl font-bold mb-4">
          Ready to Summarize Your Content?
        </h2>
        <p className="text-xl mb-8 opacity-90">
          Get started in seconds. Process text and document files instantly.
        </p>
        <Link to="/generate">
          <button className="bg-white text-primary-600 hover:bg-gray-100 font-medium px-8 py-3 rounded-lg transition-colors text-lg">
            Start Summarizing Now
          </button>
        </Link>
      </section>
    </div>
  );
};

export default Home;
