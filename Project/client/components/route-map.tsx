'use client'

import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

interface RouteMapProps {
  origin: { latitude: number; longitude: number }
  destination: { latitude: number; longitude: number }
}

export function RouteMap({ origin, destination }: RouteMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)

  const originMarker = useRef<mapboxgl.Marker | null>(null)
  const destinationMarker = useRef<mapboxgl.Marker | null>(null)

  useEffect(() => {
    if (!mapContainer.current) return

    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN
    if (!token) return

    mapboxgl.accessToken = token

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [origin.longitude, origin.latitude],
      zoom: 12,
    })

    map.current.on('load', async () => {
      if (!map.current) return

      // Create custom pointer element
      const el = document.createElement('div')
      el.style.width = '24px'
      el.style.height = '24px'
      el.style.borderRadius = '50%'
      el.style.backgroundColor = '#3b82f6'
      el.style.border = '3px solid white'
      el.style.boxShadow = '0 0 10px rgba(0,0,0,0.3)'
      el.style.cursor = 'pointer'

      // Add origin marker with custom element
      originMarker.current = new mapboxgl.Marker({ element: el })
        .setLngLat([origin.longitude, origin.latitude])
        .addTo(map.current)

      // Add destination marker
      destinationMarker.current = new mapboxgl.Marker({ color: '#ef4444' })
        .setLngLat([destination.longitude, destination.latitude])
        .setPopup(new mapboxgl.Popup().setHTML('<p>Destination</p>'))
        .addTo(map.current)

      // Fetch and add route
      await updateRoute()
    })

    return () => {
      map.current?.remove()
    }
  }, [])

  useEffect(() => {
    if (!map.current || !originMarker.current) return
    
    // Smoothly animate marker to new position
    originMarker.current.setLngLat([origin.longitude, origin.latitude])
    
    // Update route
    updateRoute()
  }, [origin])

  useEffect(() => {
    if (!map.current || !destinationMarker.current) return
    
    // Update destination marker position
    destinationMarker.current.setLngLat([destination.longitude, destination.latitude])
    
    // Update route when destination changes
    updateRoute()
  }, [destination])

  const updateRoute = async () => {
    if (!map.current) return
    
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN
    if (!token) return

    try {
      const query = await fetch(
        `https://api.mapbox.com/directions/v5/mapbox/driving/${origin.longitude},${origin.latitude};${destination.longitude},${destination.latitude}?geometries=geojson&access_token=${token}`
      )
      const json = await query.json()
      const route = json.routes[0].geometry

      const source = map.current.getSource('route') as mapboxgl.GeoJSONSource
      if (source) {
        source.setData({
          type: 'Feature',
          properties: {},
          geometry: route,
        })
      } else {
        map.current.addSource('route', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: route,
          },
        })

        map.current.addLayer({
          id: 'route',
          type: 'line',
          source: 'route',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#3b82f6',
            'line-width': 4,
          },
        })
      }
    } catch (error) {
      console.error('Error updating route:', error)
    }
  }

  return <div ref={mapContainer} className="w-full h-full" />
}
