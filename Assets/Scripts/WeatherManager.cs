using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using TMPro;

//Bring Openweather JSON File 
[Serializable]
public class WeatherData
{
    public Weather[] weather; // Weather state
    public MainData main;     // Temperature, Humidity
    public string name;       // City name
}

[Serializable]
public class Weather
{
    public string main;
    public string description;
}

[Serializable]
public class MainData
{
    public float temp;        // current temperature
    public float feels_like;  // Feels like temperature 
    public int humidity;      
}

public class WeatherManager : MonoBehaviour
{
    [Header("Setting")]
    public string apiKey = "0890efcc3e033a7aa2e6003c7d6fc296";
    public string cityName = "Seoul";

    public TextMeshProUGUI WeatherText;

    void Start()
    {
        StartCoroutine(GetWeatherEveryHour());
    }

    IEnumerator GetWeatherEveryHour()
    {
        while(true)
        {
            yield return StartCoroutine(GetWeatherRoutine());

            Debug.Log("wait 1 hour");
            yield return new WaitForSeconds(3600f);
        }
    }

    IEnumerator GetWeatherRoutine()
    {
        // use url 
        string url = $"https://api.openweathermap.org/data/2.5/weather?q={cityName}&appid={apiKey}&units=metric";

        using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError || webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("error occur: " + webRequest.error);
            }
            else
            {
                // 
                string json = webRequest.downloadHandler.text;
                WeatherData data = JsonUtility.FromJson<WeatherData>(json);

                /*
                Debug.Log($"[{data.name}]");
                Debug.Log($"{data.weather[0].main} ({data.weather[0].description})");
                Debug.Log($" {data.main.temp}¡ÆC /  {data.main.feels_like}¡ÆC");
                Debug.Log($"{data.main.humidity}%");
                */
                WeatherText.text = $"City:{cityName} Weather:{data.weather[0].main}\nTemperature:{data.main.temp}¡ÆC\nFeels like temperature:{data.main.feels_like}¡ÆC\nHumidity:{data.main.humidity}%";
            }
        }
    }
}
