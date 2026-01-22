import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileAudio, Clock, Download, Trash2, Plus, FolderOpen } from 'lucide-react';

const Projects = () => {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = () => {
    const saved = JSON.parse(localStorage.getItem('podcastProjects') || '[]');
    setProjects(saved);
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      const updated = projects.filter(p => p.id !== id);
      localStorage.setItem('podcastProjects', JSON.stringify(updated));
      setProjects(updated);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            My Projects
          </h1>
          <p className="text-gray-600">
            View and manage your recent podcast projects
          </p>
        </div>
        <Link to="/generate">
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-5 h-5" />
            New Project
          </button>
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="card text-center py-16">
          <FolderOpen className="w-20 h-20 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            No projects yet
          </h3>
          <p className="text-gray-500 mb-6">
            Create your first podcast project to get started
          </p>
          <Link to="/generate">
            <button className="btn-primary inline-flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Create Project
            </button>
          </Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div
              key={project.id}
              className="card hover:shadow-xl transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="bg-primary-100 p-3 rounded-lg">
                  <FileAudio className="w-8 h-8 text-primary-600" />
                </div>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-success-100 text-success-700">
                  {project.status}
                </span>
              </div>

              <h3 className="font-semibold text-gray-900 mb-2 truncate text-lg">
                {project.pdfName}
              </h3>

              <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                <Clock className="w-4 h-4" />
                {formatDate(project.createdAt)}
              </div>

              <div className="text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Host:</span>
                  <span className="font-medium capitalize">{project.hostVoice}</span>
                </div>
                <div className="flex justify-between">
                  <span>Guest:</span>
                  <span className="font-medium capitalize">{project.guestVoice}</span>
                </div>
              </div>

              <div className="flex gap-2 pt-4 border-t border-gray-100">
                <a
                  href={project.audioUrl}
                  download
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </a>
                <button
                  onClick={() => handleDelete(project.id)}
                  className="btn-secondary p-3"
                  title="Delete project"
                >
                  <Trash2 className="w-4 h-4 text-error-600" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Projects;
