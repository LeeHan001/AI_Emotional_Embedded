using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class ExpressionManager : MonoBehaviour
{
    public Animator Anim;
    public bool isTouch = false;
    public bool isNight;

    public TextMeshProUGUI EmotionConfidenceRate;
    public SocketManager WebSocket;

    public GameObject ConnectOnImage;
    public GameObject ConnectOffImage;

    private void Start()
    {
        StartCoroutine(EmotionDetect());
    }
    IEnumerator EmotionDetect()
    {
        while(true)
        {
            if(WebSocket.WebSocketConnect)
            {
                ConnectOnImage.SetActive(true);
                ConnectOffImage.SetActive(false);
                Anim.SetBool("FindFace", WebSocket.FaceCheck);
                Anim.SetBool("IsNight", WebSocket.DayNightCheck);
                Anim.SetInteger("IntEmotion", WebSocket.FaceValue);
                EmotionConfidenceRate.text = $"Time : {WebSocket.DayNightName}\nEmotion : {WebSocket.FaceName}\nProbability : {WebSocket.Probability}";
            }    
            else
            {
                ConnectOnImage.SetActive(false);
                ConnectOffImage.SetActive(true);
                Anim.SetBool("FindFace", false);
                Anim.SetBool("IsNight", false);
                EmotionConfidenceRate.text = $"Can't connect\nWebSocket...";
            }
            yield return new WaitForSeconds(0.25f);
        }
    }


    IEnumerator BackIdel()
    {
        yield return new WaitForSeconds(2f);

        isTouch = false;
        Anim.SetBool("OnTouch", isTouch);
    }
    public void Touch()
    {
        StopAllCoroutines();

        isTouch = !isTouch;
        Anim.SetBool("OnTouch", isTouch);
        int RandomIndex = Random.Range(0, 11);

        Anim.SetInteger("IntRandomEmotion", RandomIndex);

        StartCoroutine(BackIdel());
    }
}
