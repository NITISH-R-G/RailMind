import httpx # type: ignore
import os
from datetime import datetime
from dotenv import load_dotenv

# Ensure env variables are loaded
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

RAILWAYS_API_KEY = os.getenv("RAILWAYS_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com")

BASE_URL = "https://indianrailapi.com/api/v2"

STATION_COORDS = {
    # North India
    "NDLS": {"lat": 28.6419, "lng": 77.2194, "name": "New Delhi"},
    "DLI": {"lat": 28.6562, "lng": 77.2410, "name": "Delhi Junction"},
    "CNB": {"lat": 26.4499, "lng": 80.3319, "name": "Kanpur Central"},
    "LKO": {"lat": 26.8467, "lng": 80.9462, "name": "Lucknow"},
    "ALD": {"lat": 25.4358, "lng": 81.8463, "name": "Prayagraj"},
    "BSB": {"lat": 25.3176, "lng": 82.9739, "name": "Varanasi"},
    "GKP": {"lat": 26.7606, "lng": 83.3732, "name": "Gorakhpur"},
    "AGC": {"lat": 27.1767, "lng": 78.0081, "name": "Agra Cantt"},
    "MTJ": {"lat": 27.4924, "lng": 77.6737, "name": "Mathura"},
    "ALJN": {"lat": 27.8974, "lng": 78.0880, "name": "Aligarh"},
    "MB": {"lat": 28.9845, "lng": 77.7064, "name": "Moradabad"},
    "SRE": {"lat": 29.9691, "lng": 77.5469, "name": "Saharanpur"},
    "AMB": {"lat": 30.3782, "lng": 76.7767, "name": "Ambala"},
    "ASR": {"lat": 31.6340, "lng": 74.8723, "name": "Amritsar"},
    "LDH": {"lat": 30.9010, "lng": 75.8573, "name": "Ludhiana"},
    "UMB": {"lat": 30.9167, "lng": 76.9500, "name": "Ambala Cantt"},
    "HW": {"lat": 29.9457, "lng": 78.1642, "name": "Haridwar"},
    "DDN": {"lat": 30.3165, "lng": 78.0322, "name": "Dehradun"},

    # Bihar & Jharkhand
    "PNBE": {"lat": 25.6093, "lng": 85.1235, "name": "Patna"},
    "RJPB": {"lat": 25.6093, "lng": 85.1390, "name": "Rajendra Nagar"},
    "BGP": {"lat": 25.2425, "lng": 86.9842, "name": "Bhagalpur"},
    "MFP": {"lat": 26.1197, "lng": 85.3910, "name": "Muzaffarpur"},
    "DBG": {"lat": 26.1522, "lng": 85.8970, "name": "Darbhanga"},
    "SPJ": {"lat": 25.8645, "lng": 85.7810, "name": "Samastipur"},
    "DHN": {"lat": 23.7957, "lng": 86.4304, "name": "Dhanbad"},
    "JSME": {"lat": 24.1540, "lng": 86.2028, "name": "Jasidih"},
    "RNC": {"lat": 23.3441, "lng": 85.3096, "name": "Ranchi"},

    # West Bengal
    "HWH": {"lat": 22.5958, "lng": 88.2636, "name": "Howrah"},
    "SDAH": {"lat": 22.5697, "lng": 88.3697, "name": "Sealdah"},
    "KOAA": {"lat": 22.5726, "lng": 88.3639, "name": "Kolkata"},
    "BDC": {"lat": 22.8456, "lng": 88.3632, "name": "Bandel"},
    "BWN": {"lat": 23.2324, "lng": 87.8615, "name": "Bardhaman"},
    "KGP": {"lat": 22.3460, "lng": 87.3195, "name": "Kharagpur"},

    # Maharashtra
    "CSTM": {"lat": 18.9398, "lng": 72.8355, "name": "Mumbai CST"},
    "BCT": {"lat": 18.9690, "lng": 72.8205, "name": "Mumbai Central"},
    "LTT": {"lat": 19.0668, "lng": 72.9244, "name": "Lokmanya Tilak"},
    "PUNE": {"lat": 18.5286, "lng": 73.8742, "name": "Pune"},
    "NGP": {"lat": 21.1458, "lng": 79.0882, "name": "Nagpur"},
    "AWB": {"lat": 19.8762, "lng": 75.3433, "name": "Aurangabad"},
    "NED": {"lat": 19.1566, "lng": 77.3212, "name": "Nanded"},
    "SUR": {"lat": 17.6868, "lng": 75.9064, "name": "Solapur"},

    # Karnataka
    "SBC": {"lat": 12.9784, "lng": 77.5736, "name": "Bangalore City"},
    "YPR": {"lat": 13.0148, "lng": 77.5510, "name": "Yesvantpur"},
    "UBL": {"lat": 15.3647, "lng": 75.1240, "name": "Hubli"},
    "MYS": {"lat": 12.2958, "lng": 76.6394, "name": "Mysuru"},

    # Tamil Nadu
    "MAS": {"lat": 13.0827, "lng": 80.2707, "name": "Chennai Central"},
    "MS": {"lat": 13.0012, "lng": 80.2565, "name": "Chennai Egmore"},
    "TPJ": {"lat": 10.7905, "lng": 78.7047, "name": "Tiruchirappalli"},
    "MDU": {"lat": 9.9252, "lng": 78.1198, "name": "Madurai"},
    "CBE": {"lat": 11.0168, "lng": 76.9558, "name": "Coimbatore"},
    "NCJ": {"lat": 8.7139, "lng": 77.7567, "name": "Nagercoil"},

    # Kerala
    "TVC": {"lat": 8.4855, "lng": 76.9492, "name": "Thiruvananthapuram"},
    "ERS": {"lat": 9.9816, "lng": 76.2999, "name": "Ernakulam"},
    "CLT": {"lat": 11.2588, "lng": 75.7804, "name": "Kozhikode"},
    "SRR": {"lat": 10.9598, "lng": 75.9495, "name": "Shoranur"},

    # Andhra Pradesh & Telangana
    "SC": {"lat": 17.4339, "lng": 78.5000, "name": "Secunderabad"},
    "HYB": {"lat": 17.3850, "lng": 78.4867, "name": "Hyderabad"},
    "BZA": {"lat": 16.5193, "lng": 80.6305, "name": "Vijayawada"},
    "VSKP": {"lat": 17.7231, "lng": 83.2985, "name": "Visakhapatnam"},
    "GNT": {"lat": 16.3067, "lng": 80.4365, "name": "Guntur"},

    # Gujarat
    "ADI": {"lat": 23.0225, "lng": 72.5714, "name": "Ahmedabad"},
    "BRC": {"lat": 22.3144, "lng": 73.1932, "name": "Vadodara"},
    "ST": {"lat": 21.1702, "lng": 72.8311, "name": "Surat"},
    "RJT": {"lat": 22.3039, "lng": 70.8022, "name": "Rajkot"},

    # Madhya Pradesh
    "BPL": {"lat": 23.2599, "lng": 77.4126, "name": "Bhopal"},
    "JBP": {"lat": 23.1815, "lng": 79.9864, "name": "Jabalpur"},
    "GWL": {"lat": 26.2183, "lng": 78.1828, "name": "Gwalior"},
    "INDB": {"lat": 22.7196, "lng": 75.8577, "name": "Indore"},
    "ET": {"lat": 23.6611, "lng": 77.7631, "name": "Itarsi"},

    # Rajasthan
    "JP": {"lat": 26.9124, "lng": 75.7873, "name": "Jaipur"},
    "AII": {"lat": 26.4499, "lng": 74.6399, "name": "Ajmer"},
    "JU": {"lat": 26.2389, "lng": 73.0243, "name": "Jodhpur"},
    "BKN": {"lat": 28.0229, "lng": 73.3119, "name": "Bikaner"},
    "UDZ": {"lat": 24.5713, "lng": 73.6915, "name": "Udaipur"},

    # Odisha
    "BBS": {"lat": 20.2961, "lng": 85.8189, "name": "Bhubaneswar"},
    "CTC": {"lat": 20.4625, "lng": 85.8830, "name": "Cuttack"},
    "PURI": {"lat": 19.8135, "lng": 85.8312, "name": "Puri"},

    # Assam & Northeast
    "GHY": {"lat": 26.1445, "lng": 91.7362, "name": "Guwahati"},
    "DBRG": {"lat": 27.4728, "lng": 95.0152, "name": "Dibrugarh"},
}

def parse_rapidapi_train_for_agent(data: dict, train_number: str) -> dict:
    outer_data = data.get("data", {})
    if not outer_data:
        return {}
    
    t_num = outer_data.get("train_number", train_number)
    t_name = outer_data.get("train_name", t_num)
    
    station_code = outer_data.get("current_station_code", "Unknown")
    coords = STATION_COORDS.get(station_code, {"lat": 20.5937, "lng": 78.9629, "name": "Unknown"})
    
    current_station = outer_data.get("current_station_name", "Unknown").replace("~", "").strip()
    if current_station == "Unknown" and coords.get("name") != "Unknown":
        current_station = coords["name"]
    
    delay_minutes = 0
    try:
        delay_minutes = int(outer_data.get("delay", 0))
    except:
        pass

    if delay_minutes == 0:
        passenger_load = "normal"
    elif delay_minutes <= 15:
        passenger_load = "medium"
    elif delay_minutes <= 30:
        passenger_load = "high"
    else:
        passenger_load = "overcrowded"

    status = "on_time"
    if delay_minutes > 60:
        status = "severely_delayed"
    elif delay_minutes > 15:
        status = "delayed"
        
    title = str(outer_data.get("title", "")).lower()
    if "complete" in title or "reached" in title:
        status = "reached"
        
    lat = coords["lat"]
    lng = coords["lng"]
        
    return {
        "train_number": t_num,
        "train_name": t_name,
        "current_station": current_station,
        "station_code": station_code,
        "delay_minutes": delay_minutes,
        "passenger_load": passenger_load,
        "status": status,
        "schedule_arrival": outer_data.get("cur_stn_sta", "-"),
        "actual_arrival": outer_data.get("eta", "-"),
        "source": outer_data.get("source_stn_name", "Unknown"),
        "destination": outer_data.get("dest_stn_name", "Unknown"),
        "lat": lat,
        "lng": lng
    }

RAW_MOCK_TRAINS = {
    "12301": {
        "train_number": "12301",
        "train_name": "Howrah Rajdhani Express",
        "source": "NDLS",
        "destination": "HWH",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "HOWRAH JN",
        "title": "Delayed at Kanpur Central",
        "delay": 45,
        "current_station_code": "CNB",
        "current_station_name": "Kanpur Central",
        "cur_stn_lat": "26.4499",
        "cur_stn_lng": "80.3319",
        "cur_stn_sta": "10:05",
        "eta": "10:50",
        "gps_unable": False
    },
    "12951": {
        "train_number": "12951",
        "train_name": "Mumbai Rajdhani Express",
        "source": "NDLS",
        "destination": "MMCT",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "MUMBAI CENTRAL",
        "title": "Delayed at Bhopal",
        "delay": 22,
        "current_station_code": "BPL",
        "current_station_name": "Bhopal",
        "cur_stn_lat": "23.2599",
        "cur_stn_lng": "77.4126",
        "cur_stn_sta": "08:35",
        "eta": "08:57",
        "gps_unable": False
    },
    "12001": {
        "train_number": "12001",
        "train_name": "Bhopal Shatabdi Express",
        "source": "NDLS",
        "destination": "RKMP",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "RANI KAMLAPATI",
        "title": "Nominal delay at Agra",
        "delay": 8,
        "current_station_code": "AGC",
        "current_station_name": "Agra Cantt",
        "cur_stn_lat": "27.1767",
        "cur_stn_lng": "78.0081",
        "cur_stn_sta": "14:40",
        "eta": "14:48",
        "gps_unable": False
    },
    "12259": {
        "train_number": "12259",
        "train_name": "Sealdah Duronto Express",
        "source": "NDLS",
        "destination": "SDAH",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "SEALDAH",
        "title": "Delayed at Bardhaman",
        "delay": 67,
        "current_station_code": "BWN",
        "current_station_name": "Bardhaman",
        "cur_stn_lat": "23.2324",
        "cur_stn_lng": "87.8615",
        "cur_stn_sta": "16:15",
        "eta": "17:22",
        "gps_unable": False
    },
    "12565": {
        "train_number": "12565",
        "train_name": "Bihar Sampark Kranti Express",
        "source": "DBG",
        "destination": "NDLS",
        "source_stn_name": "DARBHANGA JN",
        "dest_stn_name": "NEW DELHI",
        "title": "Delayed at Gorakhpur",
        "delay": 34,
        "current_station_code": "GKP",
        "current_station_name": "Gorakhpur",
        "cur_stn_lat": "26.7606",
        "cur_stn_lng": "83.3732",
        "cur_stn_sta": "05:15",
        "eta": "05:49",
        "gps_unable": False
    },
    "11057": {
        "train_number": "11057",
        "train_name": "Amritsar Express",
        "source": "CSMT",
        "destination": "ASR",
        "source_stn_name": "MUMBAI CSMT",
        "dest_stn_name": "AMRITSAR JN",
        "title": "Delayed at Ludhiana",
        "delay": 15,
        "current_station_code": "LDH",
        "current_station_name": "Ludhiana",
        "cur_stn_lat": "30.9010",
        "cur_stn_lng": "75.8573",
        "cur_stn_sta": "20:10",
        "eta": "20:25",
        "gps_unable": False
    },
    "12627": {
        "train_number": "12627",
        "train_name": "Karnataka Express",
        "source": "NDLS",
        "destination": "SBC",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "KSR BENGALURU",
        "title": "Delayed at Secunderabad",
        "delay": 51,
        "current_station_code": "SC",
        "current_station_name": "Secunderabad",
        "cur_stn_lat": "17.4339",
        "cur_stn_lng": "78.5000",
        "cur_stn_sta": "18:00",
        "eta": "18:51",
        "gps_unable": False
    },
    "12625": {
        "train_number": "12625",
        "train_name": "Kerala Express",
        "source": "NDLS",
        "destination": "TVC",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "TRIVANDRUM CENTRAL",
        "title": "Delayed 89min at Nagpur",
        "delay": 89,
        "current_station_code": "NGP",
        "current_station_name": "Nagpur",
        "cur_stn_lat": "21.1458",
        "cur_stn_lng": "79.0882",
        "cur_stn_sta": "11:33",
        "eta": "13:02",
        "gps_unable": False
    },
    "12621": {
        "train_number": "12621",
        "train_name": "Tamil Nadu Express",
        "source": "NDLS",
        "destination": "MAS",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "MGR CHENNAI CENTRAL",
        "title": "Delayed at Vijayawada",
        "delay": 12,
        "current_station_code": "BZA",
        "current_station_name": "Vijayawada",
        "cur_stn_lat": "16.5193",
        "cur_stn_lng": "80.6305",
        "cur_stn_sta": "06:00",
        "eta": "06:12",
        "gps_unable": False
    },
    "12615": {
        "train_number": "12615",
        "train_name": "Grand Trunk Express",
        "source": "NDLS",
        "destination": "MAS",
        "source_stn_name": "NEW DELHI",
        "dest_stn_name": "MGR CHENNAI CENTRAL",
        "title": "Delayed at Gwalior",
        "delay": 28,
        "current_station_code": "GWL",
        "current_station_name": "Gwalior",
        "cur_stn_lat": "26.2183",
        "cur_stn_lng": "78.1828",
        "cur_stn_sta": "04:30",
        "eta": "04:58",
        "gps_unable": False
    },
    "12309": {
        "train_number": "12309",
        "train_name": "Patna Express",
        "source": "RJPB",
        "destination": "NDLS",
        "source_stn_name": "RAJENDRA NAGAR T",
        "dest_stn_name": "NEW DELHI",
        "title": "Delayed at Patna",
        "delay": 43,
        "current_station_code": "PNBE",
        "current_station_name": "Patna",
        "cur_stn_lat": "25.6093",
        "cur_stn_lng": "85.1235",
        "cur_stn_sta": "17:15",
        "eta": "17:58",
        "gps_unable": False
    },
    "12721": {
        "train_number": "12721",
        "train_name": "Andhra Pradesh Express",
        "source": "VSKP",
        "destination": "NDLS",
        "source_stn_name": "VISAKHAPATNAM",
        "dest_stn_name": "NEW DELHI",
        "title": "Delayed at Visakhapatnam",
        "delay": 19,
        "current_station_code": "VSKP",
        "current_station_name": "Visakhapatnam",
        "cur_stn_lat": "17.7231",
        "cur_stn_lng": "83.2985",
        "cur_stn_sta": "21:00",
        "eta": "21:19",
        "gps_unable": False
    },
    "12229": {
        "train_number": "12229",
        "train_name": "Lucknow Mail",
        "source": "LJN",
        "destination": "NDLS",
        "source_stn_name": "LUCKNOW NE",
        "dest_stn_name": "NEW DELHI",
        "title": "Delayed at Moradabad",
        "delay": 37,
        "current_station_code": "MB",
        "current_station_name": "Moradabad",
        "cur_stn_lat": "28.9845",
        "cur_stn_lng": "77.7064",
        "cur_stn_sta": "22:00",
        "eta": "22:37",
        "gps_unable": False
    },
    "12311": {
        "train_number": "12311",
        "train_name": "Kalka Mail",
        "source": "HWH",
        "destination": "KLK",
        "source_stn_name": "HOWRAH JN",
        "dest_stn_name": "KALKA",
        "title": "Nominal delay at Ambala Cantt",
        "delay": 6,
        "current_station_code": "UMB",
        "current_station_name": "Ambala Cantt",
        "cur_stn_lat": "30.9167",
        "cur_stn_lng": "76.9500",
        "cur_stn_sta": "03:00",
        "eta": "03:06",
        "gps_unable": False
    },
    "12641": {
        "train_number": "12641",
        "train_name": "Thirukkural Express",
        "source": "CAPE",
        "destination": "NZM",
        "source_stn_name": "KANYAKUMARI",
        "dest_stn_name": "HAZRAT NIZAMUDDIN",
        "title": "Delayed 71min at Madurai",
        "delay": 71,
        "current_station_code": "MDU",
        "current_station_name": "Madurai",
        "cur_stn_lat": "9.9252",
        "cur_stn_lng": "78.1198",
        "cur_stn_sta": "13:00",
        "eta": "14:11",
        "gps_unable": False
    }
}

def get_mock_rapidapi_train(train_number: str) -> dict:
    t_data = RAW_MOCK_TRAINS.get(train_number)
    if t_data:
        return {
            "status": True,
            "message": "Success",
            "data": t_data
        }
    return {
        "status": True,
        "message": "Success",
        "data": {
            "success": True,
            "train_number": train_number,
            "train_name": f"Train {train_number}",
            "gps_unable": False,
            "source": "NDLS",
            "destination": "NDLS",
            "source_stn_name": "NEW DELHI",
            "dest_stn_name": "NEW DELHI",
            "title": "Nominal",
            "delay": 0,
            "current_station_code": "NDLS",
            "current_station_name": "NEW DELHI",
            "cur_stn_lat": "28.6139",
            "cur_stn_lng": "77.2090",
            "cur_stn_sta": "12:00",
            "eta": "12:00",
            "previous_stations": []
        }
    }

def mock_train_data() -> list:
    res = []
    for tn, t_data in RAW_MOCK_TRAINS.items():
        delay = t_data.get("delay", 0)
        if delay == 0:
            load = "normal"
            status = "On Time"
        elif delay <= 15:
            load = "medium"
            status = "Delayed"
        elif delay <= 30:
            load = "high"
            status = "Delayed"
        else:
            load = "overcrowded"
            status = "Delayed"
            
        code = t_data.get("current_station_code", "Unknown")
        coords = STATION_COORDS.get(code, {"lat": 20.5937, "lng": 78.9629, "name": "Unknown"})
        current_station = coords.get("name") if coords.get("name") != "Unknown" else t_data["current_station_name"].replace("~", "").strip()
        
        res.append({
            "train_number": tn,
            "train_name": t_data["train_name"],
            "source": t_data["source"],
            "destination": t_data["destination"],
            "source_stn_name": t_data["source_stn_name"],
            "dest_stn_name": t_data["dest_stn_name"],
            "scheduled_arrival": t_data["cur_stn_sta"],
            "actual_arrival": t_data["eta"],
            "delay_minutes": delay,
            "status": status,
            "platform": "1",
            "passenger_load": load,
            "current_station": current_station,
            "lat": coords["lat"],
            "lng": coords["lng"]
        })
    return res

async def get_live_train_status(train_number: str) -> dict:
    # If RapidAPI configuration is present, use it as primary provider
    if RAPIDAPI_KEY and RAPIDAPI_KEY not in ["", "your_key_here"]:
        url = f"https://{RAPIDAPI_HOST}/api/v1/liveTrainStatus"
        params = {"trainNo": train_number, "startDay": "0"}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code != 200:
                    print(f"[RAILMIND] RapidAPI non-200 response for {train_number}: {response.status_code} - {response.text}")
                    mock_data = get_mock_rapidapi_train(train_number)
                    return parse_rapidapi_train_for_agent(mock_data, train_number)
                data = response.json()
                if data.get("status") is True:
                    return parse_rapidapi_train_for_agent(data, train_number)
                else:
                    print(f"[RAILMIND] RapidAPI failed status for {train_number}: {data}")
                    mock_data = get_mock_rapidapi_train(train_number)
                    return parse_rapidapi_train_for_agent(mock_data, train_number)
        except Exception as e:
            print(f"[RAILMIND] RapidAPI error for {train_number}: {e}")
            mock_data = get_mock_rapidapi_train(train_number)
            return parse_rapidapi_train_for_agent(mock_data, train_number)

    # Otherwise fall back to IndianRailAPI
    date = datetime.now().strftime("%Y%m%d")
    url = f"{BASE_URL}/livetrainstatus/apikey/{RAILWAYS_API_KEY}/trainnumber/{train_number}/date/{date}/"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            data = response.json()
            if data.get("ResponseCode") == "200":
                return parse_train_for_agent(data, train_number)
            mock_data = get_mock_rapidapi_train(train_number)
            return parse_rapidapi_train_for_agent(mock_data, train_number)
    except Exception as e:
        print(f"[RAILMIND] Railways API error for {train_number}: {e}")
        mock_data = get_mock_rapidapi_train(train_number)
        return parse_rapidapi_train_for_agent(mock_data, train_number)

async def get_cancelled_trains() -> list:
    date = datetime.now().strftime("%Y%m%d")
    url = f"https://indianrailapi.com/api/v2/CancelledTrains/apikey/{RAILWAYS_API_KEY}/Date/{date}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("Trains", [])
    except Exception as e:
        print(f"[RAILMIND] Cancelled trains API error: {e}")
    
    # Return mock cancelled trains if API fails or is unconfigured
    return [
        {
            "TrainNo": "12303",
            "TrainName": "Howrah - New Delhi Poorva Express",
            "Source": "HWH",
            "Destination": "NDLS",
            "Type": "Superfast"
        },
        {
            "TrainNo": "12260",
            "TrainName": "Howrah Duronto Express",
            "Source": "NDLS",
            "Destination": "HWH",
            "Type": "Duronto"
        }
    ]

async def get_trains_between_stations(from_code: str, to_code: str) -> list:
    url = f"https://indianrailapi.com/api/v2/TrainBetweenStation/apikey/{RAILWAYS_API_KEY}/From/{from_code}/To/{to_code}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("Trains", [])
    except Exception as e:
        print(f"[RAILMIND] Train between stations error: {e}")
    
    # Return mock trains between stations
    return [
        {
            "TrainNo": "12301",
            "TrainName": "Howrah - New Delhi Rajdhani Express",
            "Source": "HWH",
            "Destination": "NDLS"
        },
        {
            "TrainNo": "12303",
            "TrainName": "Howrah - New Delhi Poorva Express",
            "Source": "HWH",
            "Destination": "NDLS"
        }
    ]

async def get_multiple_trains(train_numbers: list) -> list:
    import asyncio
    tasks = [get_live_train_status(tn) for tn in train_numbers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, dict) and r]

def parse_train_for_agent(data: dict, train_number: str) -> dict:
    current = data.get("CurrentStation", {})
    route = data.get("TrainRoute", [])
    
    delay_str = current.get("DelayInArrival", "0 M")
    try:
        delay_minutes = int(delay_str.split()[0]) if delay_str not in ["-", "00 M"] else 0
    except:
        delay_minutes = 0
    
    if delay_minutes == 0: passenger_load = "normal"
    elif delay_minutes <= 15: passenger_load = "medium"
    elif delay_minutes <= 30: passenger_load = "high"
    else: passenger_load = "overcrowded"

    if delay_minutes > 60: status = "severely_delayed"
    elif delay_minutes > 15: status = "delayed"
    else: status = "on_time"
    
    station_code = current.get("StationCode", "NDLS")
    coords = STATION_COORDS.get(station_code, {"lat": 20.5937, "lng": 78.9629, "name": "Unknown"})
    
    return {
        "train_number": train_number,
        "train_name": data.get("TrainNumber", train_number),
        "current_station": coords.get("name") if coords.get("name") != "Unknown" else current.get("StationName", "Unknown"),
        "station_code": station_code,
        "delay_minutes": delay_minutes,
        "passenger_load": passenger_load,
        "status": status,
        "schedule_arrival": current.get("ScheduleArrival", "-"),
        "actual_arrival": current.get("ActualArrival", "-"),
        "source": route[0]["StationName"] if route else "Unknown",
        "destination": route[-1]["StationName"] if route else "Unknown",
        "lat": coords["lat"],
        "lng": coords["lng"]
    }

class RailwaysAPIClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("RAILWAYS_API_KEY")

    async def get_live_train_status(self, train_number: str) -> dict:
        return await get_live_train_status(train_number)

    async def get_cancelled_trains(self) -> list:
        return await get_cancelled_trains()

    async def get_trains_between_stations(self, from_code: str, to_code: str) -> list:
        return await get_trains_between_stations(from_code, to_code)

    def mock_train_data(self) -> list:
        return mock_train_data()

    async def get_multiple_trains(self, train_numbers: list) -> list:
        return await get_multiple_trains(train_numbers)
