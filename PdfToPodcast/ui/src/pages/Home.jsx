import { Link } from 'react-router-dom';
import { Upload, Sparkles, Download, ArrowRight } from 'lucide-react';
import { Button } from '@components/ui';

export const Home = () => {
  const features = [
    {
      icon: Upload,
      title: 'Easy Upload',
      description: 'Simply drag and drop your PDF document to get started',
    },
    {
      icon: Sparkles,
      title: 'AI-Powered',
      description: 'Advanced AI creates natural, engaging podcast conversations',
    },
    {
      icon: Download,
      title: 'Multiple Voices',
      description: 'Choose from 6 professional AI voices for host and guest',
    },
    {
      icon: Download,
      title: 'Download & Share',
      description: 'Get high-quality MP3 audio ready to share anywhere',
    },
  ];

  const steps = [
    {
      number: 1,
      title: 'Upload PDF',
      description: 'Upload your PDF document (max 10MB)',
    },
    {
      number: 2,
      title: 'Select Voices',
      description: 'Choose AI voices for host and guest',
    },
    {
      number: 3,
      title: 'Review Script',
      description: 'Edit the generated conversation if needed',
    },
    {
      number: 4,
      title: 'Download',
      description: 'Get your podcast audio file',
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-6 py-12">
        <div className="inline-block">
          {/* Custom Hero Image - Replace src with your actual image */}
          <img
            src="/hero-image.png"
            alt="PDF to Podcast"
            className="w-48 h-48 object-contain mx-auto mb-6"
            onError={(e) => {
              // Fallback to gradient box if image not found
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'inline-block';
            }}
          />
          <div
            className="bg-gradient-to-br from-primary-600 to-secondary-600 p-4 rounded-2xl mb-6 shadow-xl"
            style={{ display: 'none' }}
          >
            <div className="w-40 h-40 bg-white rounded-lg" />
          </div>
        </div>

        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
          Transform PDFs into
          <br />
          <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
            Engaging Podcasts
          </span>
        </h1>

        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Turn any PDF document into a natural, AI-powered podcast conversation
          in minutes. Perfect for learning, content creation, and accessibility.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
          <Link to="/generate">
            <Button size="xl" icon={ArrowRight} iconPosition="right">
              Get Started
            </Button>
          </Link>
          <Link to="/projects">
            <Button size="xl" variant="outline">
              View Projects
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section>
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Why Choose PDF to Podcast?
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
        <div className="grid md:grid-cols-4 gap-8">
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
          Ready to Create Your First Podcast?
        </h2>
        <p className="text-xl mb-8 opacity-90">
          Get started in less than 5 minutes. No sign-up required.
        </p>
        <Link to="/generate">
          <Button size="xl" variant="secondary">
            Start Generating Now
          </Button>
        </Link>
      </section>
    </div>
  );
};

export default Home;
