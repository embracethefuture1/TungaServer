#include <ros/ros.h>
#include <sensor_msgs/Imu.h>
#include <sensor_msgs/NavSatFix.h>
#include <mavros_msgs/VFR_HUD.h>
#include <std_msgs/Int32.h>
#include <std_msgs/String.h>
#include <iomanip>
#include <iostream>
#include <ctime>
#include <sstream>
#include <fstream>               // لإضافة التعامل مع الملفات

sensor_msgs::NavSatFix current_gps;
sensor_msgs::Imu current_imu;
mavros_msgs::VFR_HUD current_vfr;
int current_otonom = 0;
int current_kilitlenme = 0;

void gpsCallback(const sensor_msgs::NavSatFix::ConstPtr& msg) {
    current_gps = *msg;
}

void imuCallback(const sensor_msgs::Imu::ConstPtr& msg) {
    current_imu = *msg;
}

void vfrCallback(const mavros_msgs::VFR_HUD::ConstPtr& msg) {
    current_vfr = *msg;
}

void otonomCallback(const std_msgs::Int32::ConstPtr& msg) {
    current_otonom = msg->data;
}

void kilitCallback(const std_msgs::Int32::ConstPtr& msg) {
    current_kilitlenme = msg->data;
}

int main(int argc, char **argv) {
    ros::init(argc, argv, "telemetry_json_publisher");
    ros::NodeHandle nh;

    // Publisher للـ JSON
    ros::Publisher json_pub = nh.advertise<std_msgs::String>("telemetry_json", 10);

    // فتح ملف الكتابة (append) قبل الدخول في الحلقة
    std::ofstream logfile("veriler.json", std::ios::out | std::ios::app);
    if (!logfile.is_open()) {
        ROS_ERROR("Failed to open veriler.json for writing");
        return 1;
    }

    // الاشتراك بالتوبيكات
    ros::Subscriber gps_sub   = nh.subscribe("/mavros5/global_position/global", 10, gpsCallback);
    ros::Subscriber imu_sub   = nh.subscribe("/mavros5/imu/data",               10, imuCallback);
    ros::Subscriber vfr_sub   = nh.subscribe("/mavros5/vfr_hud",               10, vfrCallback);
    ros::Subscriber oto_sub   = nh.subscribe("/iha_otonom",                   10, otonomCallback);
    ros::Subscriber kilit_sub = nh.subscribe("/kilitlenme",                   10, kilitCallback);

    ros::Rate rate(1);  // تكرار كل ثانية

    while (ros::ok()) {
        ros::spinOnce();

        // جلب الوقت الحالي
        time_t now_c = time(nullptr);
        struct tm* parts = localtime(&now_c);

        // بناء JSON كسلسلة نصية
        std::ostringstream ss;
        ss << std::fixed << std::setprecision(6);
        ss << "{\n";
        ss << "\"takim_numarasi\": 1,\n";
        ss << "\"iha_enlem\": "   << current_gps.latitude   << ",\n";
        ss << "\"iha_boylam\": "   << current_gps.longitude  << ",\n";
        ss << "\"iha_irtifa\": "   << current_gps.altitude   << ",\n";
        ss << "\"iha_dikilme\": "  << current_imu.orientation.x << ",\n";
        ss << "\"iha_yonelme\": "  << current_imu.orientation.y << ",\n";
        ss << "\"iha_yatis\": "    << current_imu.orientation.z << ",\n";
        ss << "\"iha_hiz\": "      << current_vfr.groundspeed   << ",\n";
        ss << "\"iha_batarya\": "  << current_vfr.throttle      << ",\n";
        ss << "\"iha_otonom\": "   << current_otonom             << ",\n";
        ss << "\"iha_kilitlenme\": " << current_kilitlenme       << ",\n";
        ss << "\"hedef_merkez_X\": 300,\n";
        ss << "\"hedef_merkez_Y\": 230,\n";
        ss << "\"hedef_genislik\": 30,\n";
        ss << "\"hedef_yukseklik\": 43,\n";
        ss << "\"gps_saati\": {\n";
        ss << "  \"saat\": "        << parts->tm_hour    << ",\n";
        ss << "  \"dakika\": "      << parts->tm_min     << ",\n";
        ss << "  \"saniye\": "      << parts->tm_sec     << ",\n";
        ss << "  \"milisaniة\": 0\n";
        ss << "}\n";
        ss << "}\n";

        std::string json_str = ss.str();

        // طباعة على الكونسول
        std::cout << json_str << std::endl;

        // نشر على التوبيك
        std_msgs::String out;
        out.data = json_str;
        json_pub.publish(out);

        // كتابة JSON في الملف
        logfile << json_str << std::endl;

        rate.sleep();
    }

    // غلق الملف (لن يصل هنا عادةً إلا عند إغلاق النود)
    logfile.close();
    return 0;
    
    
}
