using System.Collections;
using UnityEngine;
using System;
using TMPro;


public class TimeManager : MonoBehaviour
{
    public TextMeshProUGUI TimeText;
    void Start()
    {
        StartCoroutine(GetTimeEverySecond());
    }

    IEnumerator GetTimeEverySecond()
    {
        while(true)
        {
            string date = DateTime.Now.ToString("yyyy.MM.dd");
            string day = DateTime.Now.ToString("dddd", System.Globalization.CultureInfo.InvariantCulture);
            string time = DateTime.Now.ToString("HH:mm");

            TimeText.text = $"{date}\n<size=64>{day}</size>\n{time}";

            yield return new WaitForSeconds(1f);
        }
    }
}
