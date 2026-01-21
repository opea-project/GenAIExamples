import { useState, useEffect } from 'react'
import { Folder, CheckSquare, Square, Play, Loader2, CheckCheck, XSquare, Search, AlertCircle } from 'lucide-react'
import { api } from '../services/api'

function ProjectSelector({ currentJob, detectedProjects, skippedFolders, onProjectsSelected }) {
  const [selectedPaths, setSelectedPaths] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [error, setError] = useState(null)

  // Debug logging
  console.log('DEBUG ProjectSelector - skippedFolders:', skippedFolders)
  console.log('DEBUG ProjectSelector - skippedFolders type:', typeof skippedFolders)
  console.log('DEBUG ProjectSelector - skippedFolders length:', skippedFolders?.length)

  // Initialize with empty selection (better UX for large repos)
  useEffect(() => {
    if (detectedProjects && detectedProjects.length > 0) {
      // For small repos (< 10 projects), select all. For large repos, select none.
      if (detectedProjects.length <= 10) {
        setSelectedPaths(detectedProjects.map(p => p.path))
      } else {
        setSelectedPaths([])
      }
    }
  }, [detectedProjects])

  const selectAll = () => {
    const filtered = getFilteredProjects()
    setSelectedPaths(prev => {
      const newPaths = filtered.map(p => p.path)
      return Array.from(new Set([...prev, ...newPaths]))
    })
  }

  const deselectAll = () => {
    const filtered = getFilteredProjects()
    const filteredPaths = filtered.map(p => p.path)
    setSelectedPaths(prev => prev.filter(path => !filteredPaths.includes(path)))
  }

  const getFilteredProjects = () => {
    if (!detectedProjects) return []
    if (!searchQuery.trim()) return detectedProjects

    const query = searchQuery.toLowerCase()
    return detectedProjects.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.path.toLowerCase().includes(query) ||
      p.types.some(t => t.toLowerCase().includes(query))
    )
  }

  const toggleProject = (path) => {
    setError(null) // Clear error when user changes selection
    setSelectedPaths(prev => {
      if (prev.includes(path)) {
        return prev.filter(p => p !== path)
      } else {
        return [...prev, path]
      }
    })
  }

  const handleSubmit = async () => {
    if (selectedPaths.length === 0) {
      setError('Please select at least one project to document')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await api.selectProjects(currentJob, selectedPaths)
      onProjectsSelected()
    } catch (err) {
      console.error('Failed to submit project selection:', err)
      // Extract error message from backend response
      const errorMessage = err.response?.data?.detail || 'Failed to submit selection. Please try again.'
      setError(errorMessage)
      setSubmitting(false)
    }
  }

  if (!detectedProjects || detectedProjects.length === 0) {
    return null
  }

  const filteredProjects = getFilteredProjects()
  const filteredSelectedCount = filteredProjects.filter(p => selectedPaths.includes(p.path)).length

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border-2 border-purple-200 p-6">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          🔍 Multiple Projects Detected
        </h3>
        <p className="text-sm text-gray-600">
          {detectedProjects.length} project(s) Found in this repository. Select a project to generate Readme file.
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-300 rounded-lg">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search and Bulk Actions */}
      <div className="mb-4 space-y-3">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search projects by name, path, or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        {/* Bulk Selection Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            <button
              onClick={selectAll}
              className="flex items-center space-x-1 px-3 py-1.5 bg-white border border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 text-sm font-medium transition-colors"
            >
              <CheckCheck className="w-4 h-4" />
              <span>Select {searchQuery ? 'Filtered' : 'All'}</span>
            </button>
            <button
              onClick={deselectAll}
              className="flex items-center space-x-1 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              <XSquare className="w-4 h-4" />
              <span>Deselect {searchQuery ? 'Filtered' : 'All'}</span>
            </button>
          </div>
          <p className="text-sm text-gray-600">
            {selectedPaths.length} of {detectedProjects.length} selected
          </p>
        </div>
      </div>

      {/* Project List */}
      <div className="space-y-3 mb-6 max-h-96 overflow-y-auto">
        {filteredProjects.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Search className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No projects match your search criteria.</p>
          </div>
        ) : (
          filteredProjects.map((project) => {
            const isSelected = selectedPaths.includes(project.path)
            const projectTypes = project.types.join(', ')
            const isRoot = project.path === '/'

            return (
              <div
                key={project.path}
              onClick={() => toggleProject(project.path)}
              className={`
                flex items-start space-x-3 p-4 rounded-lg border-2 cursor-pointer transition-all
                ${isSelected
                  ? 'bg-white border-purple-500 shadow-md'
                  : 'bg-gray-50 border-gray-200 hover:border-purple-300'
                }
              `}
            >
              <div className="flex-shrink-0 mt-1">
                {isSelected ? (
                  <CheckSquare className="w-5 h-5 text-purple-600" />
                ) : (
                  <Square className="w-5 h-5 text-gray-400" />
                )}
              </div>

              <div className="flex-grow">
                <div className="flex items-center space-x-2">
                  <Folder className="w-5 h-5 text-purple-600" />
                  <h4 className="font-semibold text-gray-800">
                    {project.name}
                    {isRoot && <span className="text-xs ml-2 text-purple-600">(Root)</span>}
                  </h4>
                </div>

                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">Path:</span> {project.path}
                </p>

                <p className="text-sm text-gray-600">
                  <span className="font-medium">Type:</span> {projectTypes}
                </p>

                <div className="flex space-x-4 text-xs text-gray-500 mt-2">
                  <span>{project.file_count} files</span>
                  <span>{project.dir_count} directories</span>
                </div>

                {project.indicators && project.indicators.length > 0 && (
                  <div className="mt-2">
                    <div className="flex flex-wrap gap-1">
                      {project.indicators.map((indicator, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded"
                        >
                          {indicator}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })
        )}
      </div>

      {/* Skipped Folders Section */}
      {skippedFolders && skippedFolders.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
             Skipped Folders ({skippedFolders.length})
          </h4>
          <p className="text-xs text-gray-600 mb-3">
            The following folders were not detected as code projects:
          </p>
          <ul className="space-y-1">
            {skippedFolders.map((folder, idx) => (
              <li key={idx} className="text-sm text-gray-700">
                • <span className="font-medium">{folder.name}</span> - {folder.reason} <span className="text-gray-500">({folder.details})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          {selectedPaths.length} project{selectedPaths.length !== 1 ? 's' : ''} selected
        </p>

        <button
          onClick={handleSubmit}
          disabled={submitting || selectedPaths.length === 0}
          className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Generate Documentation</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default ProjectSelector
