using UnityEngine;
using NativeWebSocket;
using System;

[Serializable]
public class PacketDataWeb
{
    public bool FaceCheck;
    public float Probability;
    public int FaceValue;
    public string FaceName;
    public bool DayNightCheck;
    public string DayNightName;
}

public class SocketManager : MonoBehaviour
{
    public bool WebSocketConnect = false;

    public bool FaceCheck;
    public float Probability;
    public int FaceValue;
    public string FaceName;
    public bool DayNightCheck;
    public string DayNightName;

    WebSocket websocket;

    async void Start()
    {
        websocket = new WebSocket("ws://127.0.0.1:8080");

        websocket.OnOpen += () => Debug.Log("Connection Open.");
        websocket.OnError += (e) => Debug.Log("Error : " + e);
        websocket.OnClose += (c) => Debug.Log("Connection Close.");

        websocket.OnMessage += (bytes) =>
        {
            Debug.Log("On message");
            string jsonString = System.Text.Encoding.UTF8.GetString(bytes);
            PacketDataWeb data = JsonUtility.FromJson<PacketDataWeb>(jsonString);
            ProcessData(data);
        };

        // waiting for messages
        await websocket.Connect();
    }

    void Update()
    {
        if (websocket != null)
        {
            WebSocketConnect = (websocket.State == WebSocketState.Open);
        }
    }

    void ProcessData(PacketDataWeb data)
    {
        FaceCheck = data.FaceCheck;
        Probability = data.Probability;
        FaceValue = data.FaceValue;
        FaceName = data.FaceName;
        DayNightCheck = data.DayNightCheck;
        DayNightName = data.DayNightName;
    }

    private async void OnApplicationQuit()
    {
        await websocket.Close();
    }
}