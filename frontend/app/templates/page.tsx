'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, Eye } from 'lucide-react';
import { templateApi } from '@/lib/apiClient';
import { EmailTemplate } from '@/types';
import Loading from '@/components/Loading';
import ErrorMessage from '@/components/ErrorMessage';

export default function Templates() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject: '',
    html_content: '',
    text_content: '',
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await templateApi.getAll();
      setTemplates(response.data.results || []);
    } catch (err) {
      setError('Failed to load templates. Make sure the backend is running.');
      console.error('Templates error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await templateApi.create(formData);
      setShowForm(false);
      setFormData({ name: '', description: '', subject: '', html_content: '', text_content: '' });
      fetchTemplates();
    } catch (err) {
      alert('Failed to create template');
      console.error('Create template error:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this template?')) {
      try {
        await templateApi.delete(id);
        fetchTemplates();
      } catch (err) {
        alert('Failed to delete template');
        console.error('Delete template error:', err);
      }
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Email Templates</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-purple-700"
        >
          <Plus className="h-5 w-5 mr-2" />
          New Template
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Create Form */}
      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">Create New Template</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Template Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Subject *
              </label>
              <input
                type="text"
                required
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                HTML Content *
              </label>
              <textarea
                required
                value={formData.html_content}
                onChange={(e) => setFormData({ ...formData, html_content: e.target.value })}
                rows={8}
                placeholder="<html><body><h1>Hello {{name}}</h1></body></html>"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Plain Text Content
              </label>
              <textarea
                value={formData.text_content}
                onChange={(e) => setFormData({ ...formData, text_content: e.target.value })}
                rows={4}
                placeholder="Hello {{name}}"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div className="flex gap-4">
              <button
                type="submit"
                className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700"
              >
                Create Template
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.length === 0 ? (
          <div className="col-span-full p-8 text-center text-gray-500 bg-white rounded-lg">
            No templates found. Create your first template to get started!
          </div>
        ) : (
          templates.map((template) => (
            <div key={template.id} className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h3>
              <p className="text-sm text-gray-600 mb-4">{template.description || 'No description'}</p>
              <p className="text-sm text-gray-500 mb-4">
                <strong>Subject:</strong> {template.subject}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewTemplate(template)}
                  className="flex-1 bg-purple-100 text-purple-700 px-4 py-2 rounded-lg hover:bg-purple-200 flex items-center justify-center"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  Preview
                </button>
                <button
                  onClick={() => handleDelete(template.id)}
                  className="bg-red-100 text-red-700 px-4 py-2 rounded-lg hover:bg-red-200"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <h2 className="text-2xl font-semibold">{previewTemplate.name}</h2>
              <p className="text-gray-600">{previewTemplate.subject}</p>
            </div>
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-2">HTML Preview</h3>
              <div 
                className="border border-gray-300 rounded-lg p-4 bg-gray-50"
                dangerouslySetInnerHTML={{ __html: previewTemplate.html_content }}
              />
              {previewTemplate.text_content && (
                <>
                  <h3 className="text-lg font-semibold mb-2 mt-6">Plain Text</h3>
                  <div className="border border-gray-300 rounded-lg p-4 bg-gray-50 whitespace-pre-wrap">
                    {previewTemplate.text_content}
                  </div>
                </>
              )}
            </div>
            <div className="p-6 border-t flex justify-end">
              <button
                onClick={() => setPreviewTemplate(null)}
                className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
