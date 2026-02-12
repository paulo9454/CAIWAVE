import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  MapPin,
  Radio,
  Activity,
  DollarSign,
  BarChart3,
  Trophy,
} from "lucide-react";
import { getAuthToken } from "../../lib/auth";
import { API_URL, formatCurrency } from "../../lib/utils";

const AreaAnalyticsPage = () => {
  const [areaStats, setAreaStats] = useState(null);
  const [rankings, setRankings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedArea, setSelectedArea] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };

      const [areaRes, rankingsRes] = await Promise.all([
        axios.get(`${API_URL}/analytics/area-stats`, { headers }),
        axios.get(`${API_URL}/analytics/hotspot-rankings`, { headers }),
      ]);

      setAreaStats(areaRes.data);
      setRankings(rankingsRes.data);
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      toast.error("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="analytics-page">
      <div>
        <h1 className="text-2xl font-bold">Area Analytics</h1>
        <p className="text-neutral-400 mt-1">Track connections and revenue by location</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <MapPin className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Total Areas</p>
              <p className="text-xl font-bold">{areaStats?.total_areas || 0}</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <Radio className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Total Hotspots</p>
              <p className="text-xl font-bold">{areaStats?.total_hotspots || 0}</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Total Sessions</p>
              <p className="text-xl font-bold">{(areaStats?.total_sessions || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Total Revenue</p>
              <p className="text-xl font-bold">{formatCurrency(areaStats?.total_revenue || 0)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Area Progress Bars */}
      <div className="dashboard-card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Connections by Area
        </h2>
        {areaStats?.areas.length > 0 ? (
          <div className="space-y-4">
            {areaStats.areas.slice(0, 6).map((area, idx) => {
              const maxSessions = Math.max(...areaStats.areas.map(a => a.total_sessions));
              const percentage = maxSessions > 0 ? (area.total_sessions / maxSessions) * 100 : 0;
              const colors = ["bg-blue-500", "bg-purple-500", "bg-green-500", "bg-yellow-500", "bg-red-500", "bg-cyan-500"];
              return (
                <div key={area.constituency}>
                  <div className="flex justify-between mb-1 text-sm">
                    <span className="font-medium">{area.constituency}</span>
                    <span className="text-neutral-400">{area.total_sessions.toLocaleString()} sessions</span>
                  </div>
                  <div className="h-3 bg-neutral-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${colors[idx % colors.length]} rounded-full transition-all duration-500`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-neutral-500">No area data available</div>
        )}
      </div>

      {/* Area Details Table */}
      <div className="dashboard-card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-purple-400" />
          Area Breakdown
        </h2>
        
        {areaStats?.areas.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-neutral-400 text-sm border-b border-neutral-800">
                  <th className="py-3 px-4">Rank</th>
                  <th className="py-3 px-4">Constituency</th>
                  <th className="py-3 px-4">Hotspots</th>
                  <th className="py-3 px-4">Active</th>
                  <th className="py-3 px-4">Sessions</th>
                  <th className="py-3 px-4">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {areaStats.areas.map((area, idx) => (
                  <tr 
                    key={area.constituency} 
                    className="border-b border-neutral-800/50 hover:bg-neutral-800/30 cursor-pointer transition-colors"
                    onClick={() => setSelectedArea(selectedArea?.constituency === area.constituency ? null : area)}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {idx < 3 && (
                          <Trophy className={`w-4 h-4 ${idx === 0 ? "text-yellow-400" : idx === 1 ? "text-gray-400" : "text-orange-400"}`} />
                        )}
                        <span className="font-medium">#{idx + 1}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-medium">{area.constituency}</td>
                    <td className="py-3 px-4">{area.hotspot_count}</td>
                    <td className="py-3 px-4">
                      <span className="text-green-400">{area.active_hotspots}</span>
                    </td>
                    <td className="py-3 px-4 font-semibold">{area.total_sessions.toLocaleString()}</td>
                    <td className="py-3 px-4 font-semibold text-green-400">
                      {formatCurrency(area.total_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-neutral-500">
            <MapPin className="w-12 h-12 mx-auto mb-4 text-neutral-600" />
            <p>No area data available</p>
            <p className="text-sm mt-1">Add hotspots with location data to see analytics</p>
          </div>
        )}
      </div>

      {/* Selected Area Ward Details */}
      {selectedArea && selectedArea.wards && selectedArea.wards.length > 0 && (
        <div className="dashboard-card">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Ward Details - {selectedArea.constituency}
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {selectedArea.wards.map((ward, idx) => (
              <div 
                key={ward.ward} 
                className="p-4 bg-neutral-800/50 rounded-lg border border-neutral-700"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{ward.ward}</h3>
                  <span className="text-sm text-neutral-500">#{idx + 1}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <p className="text-neutral-500">Hotspots</p>
                    <p className="font-semibold">{ward.hotspot_count}</p>
                  </div>
                  <div>
                    <p className="text-neutral-500">Sessions</p>
                    <p className="font-semibold">{ward.total_sessions.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-neutral-500">Revenue</p>
                    <p className="font-semibold text-green-400">{formatCurrency(ward.total_revenue)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Performing Hotspots */}
      {rankings?.rankings && rankings.rankings.length > 0 && (
        <div className="dashboard-card">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-400" />
            Top Performing Hotspots
          </h2>
          <div className="space-y-3">
            {rankings.rankings.slice(0, 5).map((hotspot) => (
              <div 
                key={hotspot.id}
                className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                    hotspot.rank === 1 ? "bg-yellow-500/20 text-yellow-400" :
                    hotspot.rank === 2 ? "bg-gray-500/20 text-gray-400" :
                    hotspot.rank === 3 ? "bg-orange-500/20 text-orange-400" :
                    "bg-neutral-700 text-neutral-400"
                  }`}>
                    {hotspot.rank}
                  </div>
                  <div>
                    <p className="font-medium">{hotspot.name}</p>
                    <p className="text-sm text-neutral-500">
                      {hotspot.location_name || hotspot.constituency}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{hotspot.total_sessions.toLocaleString()} sessions</p>
                  <p className="text-sm text-green-400">{formatCurrency(hotspot.total_revenue)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AreaAnalyticsPage;
