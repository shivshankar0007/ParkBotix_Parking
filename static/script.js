// ==================== GLOBALS ====================
const API_BASE = '';
let map;
let markers = [];
let currentLotId = null;
let currentLotDistance = null;
let currentBookingId = null;
let currentAmount = 0;
let userLat = null;
let userLon = null;
let routingControl = null;
let navMap = null;
let currentSelectedSlot = null;
let currentLotIdForBooking = null;
let currentPricePerHour = null;
let refreshInterval = null;

// DOM elements
const lotsList = document.getElementById('lots-list');
const slotsPanel = document.getElementById('slots-panel');
const slotsGrid = document.getElementById('slots-grid');
const lotNameSpan = document.getElementById('lot-name');
const loadingDiv = document.getElementById('loading');
const adminLink = document.getElementById('admin-link');
const adminAdvancedLink = document.getElementById('admin-advanced-link');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const qrModal = document.getElementById('qr-modal');
const qrImage = document.getElementById('qr-image');
const paymentModal = document.getElementById('payment-modal');
const paymentAmountSpan = document.getElementById('payment-amount');
const confirmPaymentBtn = document.getElementById('confirm-payment');
const navigationModal = document.getElementById('navigation-modal');
const routeMap = document.getElementById('route-map');

// ==================== HELPER FUNCTIONS ====================
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const options = { method, headers, credentials: 'include' };
    if (body) options.body = JSON.stringify(body);
    const response = await fetch(API_BASE + endpoint, options);
    if (!response.ok) {
        let errorMsg;
        try {
            const data = await response.json();
            errorMsg = data.error || `HTTP ${response.status}`;
        } catch (e) {
            errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMsg);
    }
    return response.json();
}

async function checkAuth() {
    try {
        const res = await fetch('/api/me');
        const data = await res.json();
        if (!data.authenticated) {
            window.location.href = '/login';
            return false;
        }
        if (data.user.is_admin) {
            if (adminLink) adminLink.style.display = 'inline';
            if (adminAdvancedLink) adminAdvancedLink.style.display = 'inline';
        }
        return true;
    } catch {
        window.location.href = '/login';
        return false;
    }
}

function initMap(lat, lon) {
    if (map) map.remove();
    map = L.map('map').setView([lat, lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);
    L.marker([lat, lon], {
        icon: L.divIcon({ className: 'custom-div-icon', html: '<div style="background-color:#ffd966; width:20px; height:20px; border-radius:50%; border:3px solid white;"></div>', iconSize: [20,20], iconAnchor: [10,10] })
    }).addTo(map).bindPopup('You are here');
}

// Improved search: first try to find a parking lot by name, then geocode location
async function searchLocation(query) {
    if (!query.trim()) return;
    loadingDiv.style.display = 'block';
    try {
        // Step 1: Try to find a parking lot by name (exact or partial match)
        const lotsRes = await apiCall('/api/nearby_lots', 'POST', { lat: 0, lon: 0, radius: 1000 });
        const matchedLot = lotsRes.find(lot => lot.name.toLowerCase().includes(query.toLowerCase()));
        if (matchedLot) {
            // If a lot name matches, center map on that lot and show it
            userLat = matchedLot.latitude;
            userLon = matchedLot.longitude;
            initMap(userLat, userLon);
            loadNearbyLots(userLat, userLon, 20);
            loadingDiv.style.display = 'none';
            return;
        }
        
        // Step 2: Otherwise, geocode the location using Nominatim
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
            { signal: controller.signal }
        );
        clearTimeout(timeoutId);
        const data = await response.json();
        if (data && data.length > 0) {
            const first = data[0];
            const lat = parseFloat(first.lat);
            const lon = parseFloat(first.lon);
            userLat = lat;
            userLon = lon;
            initMap(lat, lon);
            // Use a larger radius (50 km) for city searches to cover all lots in that city
            loadNearbyLots(lat, lon, 50);
        } else {
            alert('Location not found. Try a more specific name (e.g., "Gorakhpur", "Lucknow", "NIT Delhi").');
        }
    } catch (err) {
        console.error('Search error:', err);
        alert('Search failed. Please check your internet connection or try again later.');
    } finally {
        loadingDiv.style.display = 'none';
    }
}

function useMyLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation not supported.');
        return;
    }
    loadingDiv.style.display = 'block';
    navigator.geolocation.getCurrentPosition(
        position => {
            userLat = position.coords.latitude;
            userLon = position.coords.longitude;
            initMap(userLat, userLon);
            loadNearbyLots(userLat, userLon, 20);
            loadingDiv.style.display = 'none';
        },
        error => {
            loadingDiv.style.display = 'none';
            alert('Unable to get your location. Please enable location services or use the search bar.');
            console.error('Geolocation error:', error);
        }
    );
}

function refreshDistance() {
    if (userLat && userLon) {
        loadNearbyLots(userLat, userLon, 20);
    } else {
        alert('No location set. Use "My Location" first.');
    }
}

searchBtn.addEventListener('click', () => searchLocation(searchInput.value));
searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') searchBtn.click(); });

async function loadNearbyLots(lat, lon, radius = 20) {
    loadingDiv.style.display = 'block';
    try {
        const response = await fetch('/api/nearby_lots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lon, radius })
        });
        const data = await response.json();
        if (response.ok) {
            if (data.length === 0 && radius === 20) {
                // Try with larger radius if nothing found
                loadNearbyLots(lat, lon, 50);
                return;
            }
            displayLots(data);
            addMarkers(data);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (err) {
        alert('Network error: ' + err.message);
    } finally {
        loadingDiv.style.display = 'none';
    }
}

function displayLots(lots) {
    lotsList.innerHTML = '';
    if (lots.length === 0) {
        lotsList.innerHTML = '<div class="lot-card">No parking lots found within 50 km. Try searching for a city (e.g., Lucknow, Delhi) or a specific lot name.</div>';
        return;
    }
    lots.forEach(lot => {
        const card = document.createElement('div');
        card.className = 'lot-card';
        card.onclick = () => selectLot(lot.lot_id, lot.name, lot.distance_km);
        card.innerHTML = `
            <div class="lot-name">${lot.name}</div>
            <div class="lot-location"><i class="fas fa-map-pin"></i> ${lot.location}</div>
            <div class="lot-details">
                <span class="detail-item"><i class="fas fa-car"></i> ${lot.total_slots} slots</span>
                <span class="detail-item"><i class="fas fa-tag"></i> ₹${lot.price_per_hour}/hr</span>
                <span class="detail-item"><i class="fas fa-door-open"></i> ${lot.gates} gates</span>
                <span class="detail-item"><i class="fas fa-route"></i> ${lot.distance_km} km</span>
            </div>
            ${lot.ai_monitoring ? '<div class="ai-badge"><i class="fas fa-brain"></i> AI Monitoring</div>' : ''}
            <div class="lot-actions">
                <button class="book-btn" onclick="event.stopPropagation(); selectLot('${lot.lot_id}', '${lot.name}', ${lot.distance_km})">View Slots</button>
                <button class="navigate-btn" onclick="event.stopPropagation(); showNavigationModal(${lot.latitude}, ${lot.longitude}, '${lot.name}')">Navigate</button>
            </div>
        `;
        lotsList.appendChild(card);
    });
}

function addMarkers(lots) {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    lots.forEach(lot => {
        const marker = L.marker([lot.latitude, lot.longitude]).addTo(map)
            .bindPopup(`<b>${lot.name}</b><br>${lot.location}<br>₹${lot.price_per_hour}/hr<br>${lot.distance_km} km away`);
        markers.push(marker);
    });
}

function selectLot(lotId, lotName, distance) {
    currentLotId = lotId;
    currentLotDistance = distance;
    lotNameSpan.innerHTML = `${lotName} <span class="distance-badge">${distance} km away</span>`;
    showSlots(lotId);
}

async function showSlots(lotId) {
    document.getElementById('lots-section').style.display = 'none';
    slotsPanel.style.display = 'block';
    try {
        const slots = await apiCall(`/api/lots/${lotId}/slots`);
        displaySlots(slots);
        startSlotRefresh(lotId);
    } catch (err) {
        console.error('Error loading slots:', err);
        slotsGrid.innerHTML = `<div style="color:#ffaa5e; text-align:center; padding:20px;">❌ Failed to load slots. Please refresh the page or try again later.<br>Error: ${err.message}</div>`;
    }
}

function displaySlots(slots) {
    slotsGrid.innerHTML = '';
    slots.forEach(slot => {
        let statusText = '', statusClass = '';
        if (slot.status === 'available') {
            statusText = 'Available';
            statusClass = 'available';
        } else if (slot.status === 'reserved') {
            statusText = 'Reserved';
            statusClass = 'reserved';
        } else {
            statusText = 'Occupied';
            statusClass = 'occupied';
        }
        const card = document.createElement('div');
        card.className = `slot-card ${statusClass}`;
        card.innerHTML = `
            <div><strong>${slot.slot_id}</strong></div>
            <div>${slot.zone ? 'Zone ' + slot.zone : ''}</div>
            <div>${statusText}</div>
            ${slot.status === 'available' ? '<button class="reserve-btn">Book Now</button>' : ''}
        `;
        if (slot.status === 'available') {
            card.querySelector('button').onclick = (e) => {
                e.stopPropagation();
                showBookingOptions(slot.slot_id, currentLotId, currentPricePerHour || 20);
            };
        }
        slotsGrid.appendChild(card);
    });
}

function startSlotRefresh(lotId) {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => {
        if (currentLotId) {
            showSlots(currentLotId);
        }
    }, 30000);
}

function stopSlotRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// ==================== BOOKING OPTIONS (No time picker) ====================
async function showBookingOptions(slotId, lotId, pricePerHour) {
    currentSelectedSlot = slotId;
    currentLotIdForBooking = lotId;
    currentPricePerHour = pricePerHour;
    
    document.getElementById('booking-duration').value = '1';
    document.getElementById('coupon-code').value = '';
    document.getElementById('use-points').checked = false;
    await updateBookingAmount(pricePerHour);
    
    try {
        const pointsRes = await apiCall('/api/loyalty/points');
        document.getElementById('points-display').innerHTML = `(${pointsRes.points} points available)`;
    } catch(e) { console.log(e); }
    
    document.getElementById('booking-options-modal').style.display = 'flex';
}

async function updateBookingAmount(pricePerHour) {
    const duration = parseInt(document.getElementById('booking-duration').value) || 1;
    let amount = pricePerHour * duration;
    const couponCode = document.getElementById('coupon-code').value;
    const usePoints = document.getElementById('use-points').checked;
    
    if (couponCode) {
        try {
            const res = await apiCall('/api/coupons/validate', 'POST', { code: couponCode, amount });
            if (res.valid) {
                amount = res.final_amount;
                document.getElementById('booking-amount').innerHTML = amount;
                return;
            }
        } catch(e) { console.log('Invalid coupon'); }
    }
    if (usePoints) {
        try {
            const pointsRes = await apiCall('/api/loyalty/redeem', 'POST', { points: 9999, amount });
            if (pointsRes.success) {
                amount = pointsRes.final_amount;
            }
        } catch(e) { console.log(e); }
    }
    document.getElementById('booking-amount').innerHTML = amount;
}

document.getElementById('booking-duration')?.addEventListener('change', () => updateBookingAmount(currentPricePerHour));
document.getElementById('coupon-code')?.addEventListener('input', () => updateBookingAmount(currentPricePerHour));
document.getElementById('use-points')?.addEventListener('change', () => updateBookingAmount(currentPricePerHour));

document.getElementById('confirm-booking-btn')?.addEventListener('click', async () => {
    const duration = parseInt(document.getElementById('booking-duration').value);
    const couponCode = document.getElementById('coupon-code').value;
    const usePoints = document.getElementById('use-points').checked;
    const amount = parseFloat(document.getElementById('booking-amount').innerText);
    
    if (amount === 0) {
        // Free booking
        try {
            const res = await apiCall('/api/free-booking', 'POST', {
                lot_id: currentLotIdForBooking,
                slot_id: currentSelectedSlot,
                duration_hours: duration,
                coupon_code: couponCode,
                use_points: usePoints
            });
            if (res.success) {
                alert('Free booking confirmed!');
                showQRModal(res.qr_code);
                closeBookingModal();
                location.reload();
            } else alert(res.error);
        } catch(err) { alert(err.message); }
    } else {
        // Paid booking
        try {
            let couponId = null;
            if (couponCode) {
                const couponRes = await apiCall('/api/coupons/validate', 'POST', { code: couponCode, amount });
                if (couponRes.valid) couponId = couponRes.coupon_id;
            }
            let pointsUsed = 0;
            if (usePoints) {
                const pointsRes = await apiCall('/api/loyalty/redeem', 'POST', { points: 9999, amount });
                if (pointsRes.success) pointsUsed = pointsRes.points_used;
            }
            const reserveData = await apiCall('/api/reserve', 'POST', {
                lot_id: currentLotIdForBooking,
                slot_id: currentSelectedSlot,
                duration_hours: duration,
                coupon_id: couponId,
                points_used: pointsUsed
            });
            if (reserveData.success) {
                currentBookingId = reserveData.booking_id;
                currentAmount = reserveData.amount;
                if (paymentAmountSpan) paymentAmountSpan.textContent = currentAmount;
                await loadPaymentDetails();
                document.getElementById('payment-modal').style.display = 'flex';
            }
        } catch(err) { alert(err.message); }
    }
});

function closeBookingModal() {
    document.getElementById('booking-options-modal').style.display = 'none';
}
window.closeBookingModal = closeBookingModal;

// ==================== PAYMENT & QR ====================
async function loadPaymentDetails() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        const upiId = data.upi_id;
        document.getElementById('upi-id-display').textContent = upiId;
        const amount = currentAmount;
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa=${encodeURIComponent(upiId)}&pn=ParkBotix&am=${amount}&cu=INR`;
        document.getElementById('upi-qr').src = qrUrl;
    } catch (err) {
        console.error('Error loading UPI settings:', err);
    }
}

document.getElementById('confirm-payment')?.addEventListener('click', async () => {
    if (!currentBookingId) return;
    document.getElementById('payment-modal').style.display = 'none';
    try {
        const paymentInit = await apiCall('/api/payment/initiate', 'POST', {
            booking_id: currentBookingId,
            payment_method: 'upi'
        });
        const paymentProcess = await apiCall(`/api/payment/process/${paymentInit.payment_id}`, 'POST');
        if (paymentProcess.success) {
            showQRModal(paymentProcess.qr_code);
            showSlots(currentLotId);
            const lot = await getLotDetails(currentLotId);
            if (lot) showNavigationModal(lot.latitude, lot.longitude, lot.name);
            await apiCall('/api/slot/lock', 'POST', { booking_id: currentBookingId });
            await apiCall('/api/aerr/predict', 'POST', { booking_id: currentBookingId });
        } else {
            alert('Payment successful but QR not generated.');
        }
    } catch (err) {
        alert('Payment failed: ' + err.message);
    }
});

async function getLotDetails(lotId) {
    try {
        const lots = await apiCall('/api/nearby_lots', 'POST', { lat: userLat, lon: userLon, radius: 100 });
        return lots.find(l => l.lot_id === lotId);
    } catch { return null; }
}

function showNavigationModal(lat, lon, name) {
    if (!userLat || !userLon) {
        alert('Please set your location first (use search or My Location).');
        return;
    }
    document.body.style.overflow = 'hidden';
    const modal = document.getElementById('navigation-modal');
    const mapDiv = document.getElementById('route-map');
    if (!mapDiv) return;
    modal.style.display = 'flex';
    setTimeout(() => {
        if (!navMap) {
            navMap = L.map(mapDiv).setView([lat, lon], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(navMap);
        } else {
            navMap.setView([lat, lon], 13);
            if (routingControl) navMap.removeControl(routingControl);
        }
        navMap.invalidateSize();
    }, 100);
    setTimeout(() => {
        routingControl = L.Routing.control({
            waypoints: [L.latLng(userLat, userLon), L.latLng(lat, lon)],
            routeWhileDragging: true,
            showAlternatives: true,
            lineOptions: { styles: [{ color: '#FFD966', weight: 6 }] }
        }).addTo(navMap);
    }, 200);
}

function closeNavModal() {
    document.body.style.overflow = '';
    document.getElementById('navigation-modal').style.display = 'none';
}
window.closeNavModal = closeNavModal;

function closePaymentModal() {
    document.body.style.overflow = '';
    document.getElementById('payment-modal').style.display = 'none';
}
window.closePaymentModal = closePaymentModal;

function showQRModal(qrBase64) {
    document.body.style.overflow = 'hidden';
    document.getElementById('qr-image').src = `data:image/png;base64,${qrBase64}`;
    document.getElementById('qr-modal').style.display = 'flex';
}

function closeQRModal() {
    document.body.style.overflow = '';
    document.getElementById('qr-modal').style.display = 'none';
}
window.closeQRModal = closeQRModal;

function backToLots() {
    stopSlotRefresh();
    document.getElementById('slots-panel').style.display = 'none';
    document.getElementById('lots-section').style.display = 'block';
    if (userLat && userLon) loadNearbyLots(userLat, userLon, 20);
    else alert('No location set. Please search or use My Location.');
}
window.backToLots = backToLots;

document.getElementById('logout')?.addEventListener('click', async (e) => {
    e.preventDefault();
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
});

// ==================== AI ADVICE ====================
async function getAIAdvice() {
    if (!userLat || !userLon) { alert('Please set your location first.'); return; }
    const adviceDiv = document.getElementById('ai-advice-container');
    if (!adviceDiv) return;
    adviceDiv.innerHTML = '<div style="padding:20px;text-align:center;"><i class="fas fa-spinner fa-spin"></i> Getting AI advice...</div>';
    adviceDiv.style.display = 'block';
    try {
        const response = await fetch('/api/ai/advice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: userLat, lon: userLon })
        });
        const data = await response.json();
        if (response.ok) {
            adviceDiv.innerHTML = `
                <div class="ai-card">
                    <h3><i class="fas fa-robot" style="color:#FFD966;"></i> AI Parking Assistant</h3>
                    <div style="margin-top:10px; line-height:1.6;">${data.advice.replace(/\n/g, '<br>')}</div>
                </div>
            `;
        } else {
            adviceDiv.innerHTML = `<div style="color:#ffaa5e;">Error: ${data.error}</div>`;
        }
    } catch (err) {
        adviceDiv.innerHTML = `<div style="color:#ffaa5e;">Network error: ${err.message}</div>`;
    }
}
window.getAIAdvice = getAIAdvice;

async function getCongestionAdvice() {
    if (!userLat || !userLon) { alert('Set location first'); return; }
    const adviceDiv = document.getElementById('ai-advice-container');
    adviceDiv.innerHTML = '<div class="ai-card">⏳ Predicting congestion...</div>';
    adviceDiv.style.display = 'block';
    try {
        const res = await fetch('/api/pcde/advise', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: userLat, lon: userLon })
        });
        const data = await res.json();
        adviceDiv.innerHTML = `<div class="ai-card">🚦 Congestion Forecast:<br>${data.advice}</div>`;
    } catch (err) {
        adviceDiv.innerHTML = `<div class="ai-card">Error: ${err.message}</div>`;
    }
}
window.getCongestionAdvice = getCongestionAdvice;

async function registerFingerprint() {
    const plate = prompt("Enter number plate:");
    const color = prompt("Enter color:");
    const shape = prompt("Enter shape (sedan/suv/hatchback/bike):");
    if (!plate || !color || !shape) return;
    try {
        const res = await apiCall('/api/vfap/register', 'POST', { number_plate: plate, color, shape });
        alert(res.success ? "Vehicle fingerprint registered successfully" : "Registration failed");
    } catch (err) {
        alert("Error: " + err.message);
    }
}
window.registerFingerprint = registerFingerprint;

window.useMyLocation = useMyLocation;
window.refreshDistance = refreshDistance;

// ==================== INITIALIZATION ====================
(async function() {
    if (!await checkAuth()) return;
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                userLat = position.coords.latitude;
                userLon = position.coords.longitude;
                initMap(userLat, userLon);
                loadNearbyLots(userLat, userLon, 20);
            },
            error => {
                console.warn('Geolocation failed, using default Lucknow:', error);
                userLat = 26.8467;
                userLon = 80.9462;
                initMap(userLat, userLon);
                loadNearbyLots(userLat, userLon, 20);
                loadingDiv.innerHTML = 'Location unavailable. Using Lucknow as default. Click "My Location" to retry.';
            }
        );
    } else {
        userLat = 26.8467;
        userLon = 80.9462;
        initMap(userLat, userLon);
        loadNearbyLots(userLat, userLon, 20);
        loadingDiv.innerHTML = 'Geolocation not supported. Using Lucknow as default.';
    }
    document.getElementById('congestion-btn')?.addEventListener('click', getCongestionAdvice);
    document.getElementById('fingerprint-btn')?.addEventListener('click', registerFingerprint);
})();