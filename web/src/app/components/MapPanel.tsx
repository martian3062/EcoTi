"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "@/lib/api";

type Hotspot = {
  district: string; state?: string; lat: number; lng: number;
  intensity: number; complaints: number;
};

function color(i: number) {
  return i >= 0.8 ? "#dc2626" : i >= 0.6 ? "#e11d48" : i >= 0.4 ? "#d97706" : "#b76e79";
}

export default function MapPanel() {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [updated, setUpdated] = useState<string>("");

  // live refresh every 30s
  useEffect(() => {
    const load = () =>
      api.geo().then((r) => {
        setHotspots(r.hotspots ?? []);
        setUpdated(new Date().toLocaleTimeString());
      }).catch(() => {});
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = L.map(ref.current, { attributionControl: true }).setView([22.9, 79.0], 4.6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
  }, []);

  useEffect(() => {
    const layer = layerRef.current;
    if (!layer) return;
    layer.clearLayers();
    hotspots.forEach((h) => {
      L.circleMarker([h.lat, h.lng], {
        radius: 6 + h.intensity * 18,
        color: color(h.intensity),
        fillColor: color(h.intensity),
        fillOpacity: 0.35,
        weight: 1.5,
      })
        .bindPopup(
          `<b>${h.district}</b>${h.state ? ", " + h.state : ""}<br/>` +
          `${h.complaints} complaints · intensity ${h.intensity}`
        )
        .addTo(layer);
    });
  }, [hotspots]);

  return (
    <div className="glass-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink2">Geospatial crime hotspots · live</h2>
        <span className="text-[10px] text-ink3">
          {hotspots.length} hubs {updated && `· ${updated}`}
        </span>
      </div>
      <div ref={ref} className="h-[360px] w-full overflow-hidden rounded-xl" />
    </div>
  );
}
