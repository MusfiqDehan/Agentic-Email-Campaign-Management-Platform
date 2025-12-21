'use client';

import { useEffect, useState } from 'react';
import { Mail, Users, FileText, TrendingUp } from 'lucide-react';
import { campaignApi, contactApi, templateApi } from '@/lib/apiClient';
import Loading from '@/components/Loading';
import ErrorMessage from '@/components/ErrorMessage';
import Link from 'next/link';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalCampaigns: 0,
    totalContacts: 0,
    totalTemplates: 0,
    activeCampaigns: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [campaignsRes, contactsRes, templatesRes] = await Promise.all([
          campaignApi.getAll(),
          contactApi.getAll(),
          templateApi.getAll(),
        ]);

        const campaigns = campaignsRes.data.results || [];
        const activeCampaigns = campaigns.filter((c) => c.status !== 'sent').length;

        setStats({
          totalCampaigns: campaigns.length,
          totalContacts: contactsRes.data.results?.length || 0,
          totalTemplates: templatesRes.data.results?.length || 0,
          activeCampaigns,
        });
      } catch (err) {
        setError('Failed to load dashboard data. Make sure the backend is running.');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) return <Loading />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      {error && <ErrorMessage message={error} />}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Campaigns</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalCampaigns}</p>
            </div>
            <Mail className="h-12 w-12 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Contacts</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalContacts}</p>
            </div>
            <Users className="h-12 w-12 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Email Templates</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalTemplates}</p>
            </div>
            <FileText className="h-12 w-12 text-purple-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Campaigns</p>
              <p className="text-3xl font-bold text-gray-900">{stats.activeCampaigns}</p>
            </div>
            <TrendingUp className="h-12 w-12 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/campaigns"
            className="border-2 border-blue-600 text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors text-center"
          >
            Create Campaign
          </Link>
          <Link
            href="/contacts"
            className="border-2 border-green-600 text-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-green-50 transition-colors text-center"
          >
            Add Contacts
          </Link>
          <Link
            href="/templates"
            className="border-2 border-purple-600 text-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-purple-50 transition-colors text-center"
          >
            Create Template
          </Link>
        </div>
      </div>
    </div>
  );
}
