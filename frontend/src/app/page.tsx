'use client';

import DashboardLayout from '../components/DashboardLayout';
import { Calendar, Clock, Target, TrendingUp, BookOpen, FileText, Users, Star, CheckCircle, AlertTriangle, Plus, ArrowRight, GraduationCap, DollarSign, MapPin, Award } from 'lucide-react';

export default function Home() {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Welcome back, Alex!</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">Let's continue building your college application strategy</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="bg-green-100 dark:bg-green-900/20 px-3 py-1 rounded-full">
                <span className="text-green-700 dark:text-green-300 text-sm font-medium">On Track</span>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">86%</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Overall Progress</div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-6 border border-blue-200 dark:border-blue-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 dark:text-blue-400 text-sm font-medium">Applications</p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">12</p>
                <p className="text-blue-600 dark:text-blue-400 text-sm">3 submitted</p>
              </div>
              <div className="bg-blue-200 dark:bg-blue-800 p-3 rounded-lg">
                <GraduationCap className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <div className="mt-4 bg-blue-200 dark:bg-blue-800 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '75%' }}></div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-6 border border-green-200 dark:border-green-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-600 dark:text-green-400 text-sm font-medium">Essays</p>
                <p className="text-3xl font-bold text-green-900 dark:text-green-100">8</p>
                <p className="text-green-600 dark:text-green-400 text-sm">5 completed</p>
              </div>
              <div className="bg-green-200 dark:bg-green-800 p-3 rounded-lg">
                <FileText className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <div className="mt-4 bg-green-200 dark:bg-green-800 rounded-full h-2">
              <div className="bg-green-600 h-2 rounded-full" style={{ width: '63%' }}></div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-6 border border-purple-200 dark:border-purple-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-600 dark:text-purple-400 text-sm font-medium">Test Prep</p>
                <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">1480</p>
                <p className="text-purple-600 dark:text-purple-400 text-sm">SAT Score</p>
              </div>
              <div className="bg-purple-200 dark:bg-purple-800 p-3 rounded-lg">
                <Target className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
            <div className="mt-4 bg-purple-200 dark:bg-purple-800 rounded-full h-2">
              <div className="bg-purple-600 h-2 rounded-full" style={{ width: '92%' }}></div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl p-6 border border-orange-200 dark:border-orange-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-600 dark:text-orange-400 text-sm font-medium">Deadlines</p>
                <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">15</p>
                <p className="text-orange-600 dark:text-orange-400 text-sm">days until next</p>
              </div>
              <div className="bg-orange-200 dark:bg-orange-800 p-3 rounded-lg">
                <Clock className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
            <div className="mt-4 bg-orange-200 dark:bg-orange-800 rounded-full h-2">
              <div className="bg-orange-600 h-2 rounded-full" style={{ width: '30%' }}></div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Main Activities */}
          <div className="lg:col-span-2 space-y-6">
            {/* Recent Activity */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Activity</h3>
                <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium">
                  View All
                </button>
              </div>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="bg-green-100 dark:bg-green-900/20 p-2 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 dark:text-white font-medium">Common App essay completed</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Personal statement reviewed and finalized</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">2 hours ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 dark:bg-blue-900/20 p-2 rounded-lg">
                    <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 dark:text-white font-medium">Stanford supplement started</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Working on intellectual vitality essay</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">1 day ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="bg-purple-100 dark:bg-purple-900/20 p-2 rounded-lg">
                    <Users className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 dark:text-white font-medium">Recommendation request sent</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Mrs. Johnson (AP Chemistry)</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">3 days ago</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Application Progress */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Application Progress</h3>
                <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium">
                  Manage All
                </button>
              </div>
              <div className="space-y-4">
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                        <span className="text-red-600 dark:text-red-400 font-bold text-sm">S</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">Stanford University</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Early Action • Due Dec 1</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">85%</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Complete</div>
                    </div>
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-red-600 h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                        <span className="text-blue-600 dark:text-blue-400 font-bold text-sm">MIT</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">MIT</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Regular Decision • Due Jan 1</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">65%</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Complete</div>
                    </div>
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '65%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Quick Actions</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors border border-blue-200 dark:border-blue-700/50 text-left">
                  <div className="flex items-center space-x-3">
                    <Plus className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    <div>
                      <div className="text-blue-600 dark:text-blue-400 font-medium">Add New School</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Research and add colleges</div>
                    </div>
                  </div>
                </button>
                <button className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors border border-green-200 dark:border-green-700/50 text-left">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <div>
                      <div className="text-green-600 dark:text-green-400 font-medium">Continue Essay</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Work on supplements</div>
                    </div>
                  </div>
                </button>
                <button className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors border border-purple-200 dark:border-purple-700/50 text-left">
                  <div className="flex items-center space-x-3">
                    <Users className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    <div>
                      <div className="text-purple-600 dark:text-purple-400 font-medium">Request Rec</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Contact teachers</div>
                    </div>
                  </div>
                </button>
                <button className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors border border-orange-200 dark:border-orange-700/50 text-left">
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                    <div>
                      <div className="text-orange-600 dark:text-orange-400 font-medium">View Timeline</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Check deadlines</div>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Sidebar Info */}
          <div className="space-y-6">
            {/* AI Insights */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Insights</h3>
                <div className="bg-green-100 dark:bg-green-900/20 px-2 py-1 rounded-full">
                  <span className="text-green-700 dark:text-green-300 text-xs font-medium">Active</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                  <div className="flex items-start space-x-2">
                    <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Strong Match</p>
                      <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">Your profile aligns well with UC Berkeley's engineering program</p>
                    </div>
                  </div>
                </div>
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3">
                  <div className="flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">Deadline Alert</p>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">MIT application due in 15 days</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Upcoming Deadlines */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Upcoming Deadlines</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-red-900 dark:text-red-100">Stanford EA</p>
                    <p className="text-xs text-red-700 dark:text-red-300">Essays due</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-red-600 dark:text-red-400">Dec 1</div>
                    <div className="text-xs text-red-500 dark:text-red-400">15 days</div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-orange-900 dark:text-orange-100">MIT Regular</p>
                    <p className="text-xs text-orange-700 dark:text-orange-300">Application due</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-orange-600 dark:text-orange-400">Jan 1</div>
                    <div className="text-xs text-orange-500 dark:text-orange-400">46 days</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Profile Strength */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Profile Strength</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Academics</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">95%</span>
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '95%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Extracurriculars</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">82%</span>
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '82%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Essays</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">78%</span>
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-purple-600 h-2 rounded-full" style={{ width: '78%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
