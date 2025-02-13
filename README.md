# **Fuel Route Optimization API**  

## **Overview**  
This project provides an API that calculates an optimal fuel-up route for a vehicle traveling between two locations in the USA. The goal is to **minimize fuel cost** while ensuring the vehicle never runs out of fuel. The API integrates **OpenRouteService (ORS) for route calculation** and **Mapbox for geolocation processing**.

## **Key Features**  
Fetches **optimal fuel stations** along the route.  
Ensures the **vehicle never travels more than 500 miles** without refueling.  
Selects **stations based on price** while staying **on route**.  
Uses **Haversine formula** to calculate distances between stations and the route.  
Integrates **OpenRouteService for routing** and **Mapbox for geolocation**.  
Returns the **total fuel cost** based on consumption.

---

## **1️⃣ Data Processing with Mapbox**  
### **Fuel Stations CSV & Mapbox Integration**  
Initially, the dataset **did not include latitude and longitude** for fuel stations, only their **addresses**. To obtain their coordinates, we used **Mapbox API**:

1. **Read fuel station data from CSV** (name, address, city, state, price, etc.).
2. **Query Mapbox API** to retrieve `latitude` and `longitude` for each station.
3. **Save enriched data** with coordinates into the database.

---

## **2️⃣ Route Calculation with OpenRouteService**  
### **Fetching the Route**  
The API takes **start and end coordinates** as input and queries OpenRouteService:

- ORS returns a **route with step-by-step navigation**.
- The API extracts **the route geometry** (as a polyline) and **the total distance**.

---

## **3️⃣ Optimizing Fuel Stops**  
### **Constraints Considered**  
🔹 The **vehicle has a max range of 500 miles** per fuel-up.  
🔹 The **cheapest station** within **5 miles of the route** is selected.  
🔹 The **stations must follow the route sequence** (no detours).  

### **Algorithm**  
1. Decode **route geometry (polyline)** to get **waypoints**.
2. Loop through **every 500 miles** of the route to check for **fuel stops**.
3. Select **stations within 5 miles of the route**.
4. Choose the **cheapest fuel station** within that range.
5. Move to the **next 500-mile segment** and repeat.
6. Return **all optimal stops** along with total fuel cost.

---

## **4️⃣ API Usage**  
### **Endpoint: `/fuel/api/calculate-route/`**  
#### **Request (JSON Payload)**  
```json
{
    "start_lat": 40.712776,
    "start_lon": -74.005974,
    "end_lat": 38.9072,
    "end_lon": -77.0369
}
```

#### **Response (Example Output)**  
```json
{
    "route": { ... },
    "optimal_fuel_stations": [
        {
            "id": 123,
            "name": "Best Price Gas",
            "lat": 39.856,
            "lon": -75.123,
            "price": "3.29"
        }
    ],
    "total_fuel_cost": 45.80
}
```

---

## **5️⃣ Installation & Setup**  
### **Requirements**  
- Python 3.8+
- Django
- OpenRouteService API Key
- Mapbox API Key

### **Installation**  
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### **Environment Variables**  
Set your API keys in `.env`:
```
ORS_API_KEY=your_openrouteservice_api_key
MAPBOX_API_KEY=your_mapbox_api_key
```

---

## **6️⃣ Next Steps**  
🔹 Improve performance for **longer routes**.  
🔹 Optimize station selection for **better cost savings**.  
🔹 Add **UI visualization** for route mapping.  

---

🔥 **Built with Django, OpenRouteService, and Mapbox.**

