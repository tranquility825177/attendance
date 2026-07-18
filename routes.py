from flask import render_template, request, redirect, flash, session, send_file
import secrets
import pymysql 
from config import *
import io
import qrcode
import json
import os
import base64
import numpy as np
from datetime import datetime, time
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

def get_connection():
    return pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )

def generate_qr_token():
    return secrets.token_hex(32)

def register_routes(app):

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():

        if request.method == "POST":

            aadhaar = request.form["aadhaar"].strip()
            name = request.form["name"].strip()
            email = request.form["email"].strip().lower()
            phone = request.form["phone"].strip()
            password = request.form["password"]
            hashed_password = generate_password_hash(password)
            face_descriptor = request.form["face_descriptor"]

            if not face_descriptor:
                flash("Please capture your face before registering.")
                return redirect("/register")
            
            try:
                descriptor = json.loads(face_descriptor)
                if len(descriptor) != 128:
                    flash("Invalid face descriptor.")
                    return redirect("/register")
            except Exception:
                flash("Invalid face descriptor.")
                return redirect("/register")

            # Aadhaar Validation
            if len(aadhaar) != 12 or not aadhaar.isdigit():
                flash("Aadhaar Number must contain exactly 12 digits.")
                return redirect("/register")

            # Phone Validation
            if len(phone) != 10 or not phone.isdigit():
                flash("Phone Number must contain exactly 10 digits.")
                return redirect("/register")

            conn = get_connection()
            cursor = conn.cursor()

            # Check Aadhaar
            cursor.execute(
                "SELECT id FROM officers WHERE aadhaar=%s",
                (aadhaar,)
            )

            if cursor.fetchone():
                flash("This Aadhaar Number is already registered.")
                cursor.close()
                conn.close()
                return redirect("/register")

            # Check Email
            cursor.execute(
                "SELECT id FROM officers WHERE email=%s",
                (email,)
            )

            if cursor.fetchone():
                flash("This Email is already registered.")
                cursor.close()
                conn.close()
                return redirect("/register")

            # Insert Officer
            cursor.execute("""
                INSERT INTO officers
                (aadhaar, full_name, email, phone, password, face_descriptor)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (aadhaar, name, email, phone, hashed_password, face_descriptor))

            conn.commit()

            cursor.close()
            conn.close()

            flash("Registration Successful! Please wait for Admin Approval.")

            return redirect("/")

        return render_template("register.html")
    
    @app.route("/admin", methods=["GET", "POST"])
    def admin_login():

        if request.method == "POST":

            username = request.form["username"]
            password = request.form["password"]

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""SELECT * FROM admins WHERE username=%s AND password=%s """, (username, password))

            admin = cursor.fetchone()

            cursor.close()
            conn.close()

            if admin:
                session["admin"] = username
                return redirect("/dashboard")

            flash("Invalid Username or Password")

        return render_template("admin_login.html")
    
    @app.route("/officer", methods=["GET", "POST"])
    def officer_login():

        if request.method == "POST":

            email = request.form["email"].strip().lower()
            password = request.form["password"]

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(""" SELECT * FROM officers WHERE email=%s AND status='Approved' """, (email,))

            officer = cursor.fetchone()

            cursor.close()
            conn.close()

            if officer and check_password_hash(officer["password"], password):
                session["officer"] = officer["id"]
                return redirect("/officer_dashboard")

            flash("Invalid Email or Password")

        return render_template("officer_login.html")
    
    @app.route("/officer_dashboard")
    def officer_dashboard():

        if "officer" not in session:
            return redirect("/officer")

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute(""" SELECT * FROM officers WHERE id=%s """, (session["officer"],))

        officer=cursor.fetchone()

        attendance = request.args.get("attendance")

        cursor.close()
        conn.close()

        return render_template("officer_dashboard.html", officer=officer,attendance=attendance)
    
    @app.route("/dashboard")
    def dashboard():

        if "admin" not in session:
            return redirect("/admin")

        status = request.args.get("status", "Pending")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(""" SELECT * FROM officers WHERE status=%s ORDER BY id DESC """, (status,))

        officers = cursor.fetchall()

        # Count records for dashboard
        cursor.execute("SELECT COUNT(*) AS total FROM officers WHERE status='Pending'")
        pending = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM officers WHERE status='Approved'")
        approved = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM officers WHERE status='Rejected'")
        rejected = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM officers")
        total = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        return render_template("dashboard.html",officers=officers,status=status,pending=pending,approved=approved,rejected=rejected,total=total)
    
    @app.route("/approve/<int:id>")
    def approve(id):

        if "admin" not in session:
            return redirect("/admin")

        employee_id = f"EMP{id:04d}"
        token = generate_qr_token()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(""" UPDATE officers SET status='Approved', employee_id=%s, qr_token=%s WHERE id=%s """, (employee_id, token, id))

        conn.commit()

        cursor.close()
        conn.close()
  
        flash("Officer Approved Successfully")
        return redirect("/dashboard")
    
    @app.route("/reject/<int:id>")
    def reject(id):

        if "admin" not in session:
            return redirect("/admin")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(""" UPDATE officers SET status='Rejected' WHERE id=%s """, (id,))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Officer Rejected")
        return redirect("/dashboard")
    
    @app.route("/download_qr")
    def download_qr():

        if "officer" not in session:
            return redirect("/officer")

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute(""" SELECT employee_id,qr_token FROM officers WHERE id=%s """, (session["officer"],))

        officer=cursor.fetchone()

        cursor.close()
        conn.close()

        qr_data=f"{officer['employee_id']}|{officer['qr_token']}"
        img=qrcode.make(qr_data)
        buffer=io.BytesIO()
        img.save(buffer,"PNG")
        buffer.seek(0)

        return send_file( buffer, mimetype="image/png", as_attachment=True, download_name=f"{officer['employee_id']}.png")
    
    @app.route("/attendance")
    def attendance():

        if "officer" not in session:
            return redirect("/officer")

        return render_template("attendance.html")
    
    @app.route("/verify_qr",methods=["POST"])
    def verify_qr():

        data=request.json
        employee_id=data["employee_id"]
        token=data["token"]
        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute(""" SELECT * FROM officers WHERE employee_id=%s AND qr_token=%s AND status='Approved' """,(employee_id,token))

        officer=cursor.fetchone()

        cursor.close()
        conn.close()

        if officer:
            session["attendance_officer"]=officer["id"]
            return {"success":True}

        return {"success":False}
    
    
    @app.route("/capture_face")
    def capture_face():

        if "attendance_officer" not in session:
            return redirect("/attendance")

        return render_template("capture_face.html")
    
    @app.route("/verify_face", methods=["POST"])
    def verify_face():

        if "attendance_officer" not in session:
            return {
                "success": False,
                "message": "Officer not verified."
            }

        data = request.json
        descriptor = data.get("descriptor")
        image = data.get("image")

        if not descriptor:
            return {
                "success": False,
                "message": "No face descriptor received."
            }

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT face_descriptor
            FROM officers
            WHERE id=%s
        """, (session["attendance_officer"],))

        officer = cursor.fetchone()
        if not officer:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "Officer not found."
            }
        stored_descriptor = json.loads(officer["face_descriptor"])
        live_descriptor = np.array(descriptor)
        stored_descriptor = np.array(stored_descriptor)

        distance = np.linalg.norm(live_descriptor - stored_descriptor)
        print("Distance :", distance)

        THRESHOLD = 0.50

        if distance > THRESHOLD:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "Face Verification Failed"}


        # Save Attendance Photo
        image_data = image.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        folder = "static/uploads/attendance"
        os.makedirs(folder, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        filepath = os.path.join(folder, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # Attendance Time
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        if current_time < time(11, 0):
            attendance_type = "IN"
        elif current_time >= time(17, 0):
            attendance_type = "OUT"
        else:
            cursor.close()
            conn.close()

            return {
            "success": False,
            "message": "Attendance allowed only before 11 AM or after 5 PM."}


        officer_id = session["attendance_officer"]

        # Check Existing OUT Attendance
        if attendance_type == "OUT":

            cursor.execute("""
                SELECT id
                FROM attendance
                WHERE officer_id=%s
                AND attendance_date=%s
                AND attendance_type='OUT'
            """, (officer_id, today))

            existing_out = cursor.fetchone()
        
        if existing_out:

            # Get old photo path
            cursor.execute("""
                SELECT photo_path
                FROM attendance_photos
                WHERE attendance_id=%s
            """, (existing_out["id"],))

            old_photo = cursor.fetchone()

            if old_photo:
                old_path = old_photo["photo_path"]

                if os.path.exists(old_path):
                    os.remove(old_path)

            # Update attendance time
            cursor.execute("""
                UPDATE attendance
                SET attendance_time=%s
                WHERE id=%s
            """, (current_time, existing_out["id"]))

            conn.commit()

            # Update photo path
            cursor.execute("""
                UPDATE attendance_photos
                SET photo_path=%s
                WHERE attendance_id=%s
            """, (filepath, existing_out["id"]))

            conn.commit()

            cursor.close()
            conn.close()

            return {
                "success": True,
                "attendance_type": "OUT"
            }

        # Prevent Duplicate IN
        if attendance_type == "IN":

            cursor.execute("""
                SELECT id
                FROM attendance
                WHERE officer_id=%s
                AND attendance_date=%s
                AND attendance_type='IN'
            """, (officer_id, today))

            if cursor.fetchone():
                cursor.close()
                conn.close()
                return {
                    "success": False,
                    "message": "Today's IN attendance already exists."
                }

        # Save Attendance

        cursor.execute("""
        INSERT INTO attendance(officer_id,attendance_date,attendance_type,attendance_time,face_verified,qr_verified)
        VALUES
        (%s,%s,%s,%s,%s,%s)""",
        (officer_id,today,attendance_type,current_time,1,1))

        conn.commit()
        attendance_id = cursor.lastrowid

        # Save Attendance Photo

        cursor.execute("""
        INSERT INTO attendance_photos(attendance_id,photo_path)
        VALUES
        (%s,%s)""",
        (attendance_id,filepath))

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": True,
            "attendance_type": attendance_type
        }
    
    # @app.route("/save_face", methods=["POST"])
    # def save_face():

    #     if "attendance_officer" not in session:
    #         return {"success": False}

    #     data = request.json["image"]
    #     image_data = data.split(",")[1]
    #     image_bytes = base64.b64decode(image_data)
    #     folder = "static/uploads/attendance"
    #     os.makedirs(folder, exist_ok=True)
    #     filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    #     filepath = os.path.join(folder, filename)

    #     with open(filepath, "wb") as f:
    #         f.write(image_bytes)

    #     session["captured_photo"] = filepath
        
    #     now = datetime.now()
    #     today = now.date()
    #     current_time = now.time()


    #     if current_time < time(11, 0):
    #         attendance_type = "IN"

    #     elif current_time >= time(17, 0):
    #         attendance_type = "OUT"

    #     else:
    #         return {
    #         "success": False,
    #         "message": "Attendance can only be marked before 11:00 AM or after 5:00 PM."
    #         }
        
    #     print("--------------------------------")
    #     print("Attendance Type :", attendance_type)
    #     print("Current Time :", current_time)
    #     print("--------------------------------")

    #     conn = get_connection()
    #     cursor = conn.cursor()
    #     officer_id = session["attendance_officer"]

    #     if attendance_type == "IN":

    #         cursor.execute(""" SELECT id FROM attendance WHERE officer_id=%s AND attendance_date=%s AND attendance_type='IN'
    #         """, (officer_id, today))

    #         if cursor.fetchone():
    #             cursor.close()
    #             conn.close()
    #             return {
    #                 "success": False,
    #                 "message": "Today's IN attendance is already marked."
    #             }
            
    #     cursor.execute(""" INSERT INTO attendance ( officer_id, attendance_date, attendance_type, attendance_time, face_verified, qr_verified )VALUES(%s,%s,%s,%s,%s,%s)""",( officer_id, today, attendance_type, current_time, 1, 1 ))

    #     conn.commit()
    #     attendance_id = cursor.lastrowid

    #     cursor.execute(""" INSERT INTO attendance_photos (attendance_id,photo_path) VALUES(%s,%s)""",( attendance_id, filepath ))

    #     conn.commit()
    #     cursor.close()
    #     conn.close()

    #     return {"success": True}
    

    @app.route("/attendance_report")
    def attendance_report():

        if "admin" not in session:
            return redirect("/admin")

        attendance_date = request.args.get("date")
        employee = request.args.get("employee")
        search = request.args.get("search")

        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT

            attendance.id,
            officers.employee_id,
            officers.full_name,
            attendance.attendance_date,
            attendance.attendance_type,
            attendance.attendance_time,
            attendance.face_verified,
            attendance.qr_verified,
            attendance_photos.photo_path

        FROM attendance

        JOIN officers
        ON attendance.officer_id = officers.id

        LEFT JOIN attendance_photos
        ON attendance.id = attendance_photos.attendance_id

        WHERE 1=1
        """

        values = []

        if attendance_date:
            query += " AND attendance.attendance_date=%s"
            values.append(attendance_date)

        if employee:
            query += " AND officers.id=%s"
            values.append(employee)

        if search:
            query += """
            AND
            (
                officers.employee_id LIKE %s
                OR officers.full_name LIKE %s
            )
            """
            values.append("%"+search+"%")
            values.append("%"+search+"%")

        query += " ORDER BY attendance.id DESC"

        cursor.execute(query, tuple(values))

        records = cursor.fetchall()

        # Employee dropdown data
        cursor.execute("""SELECT id, employee_id, full_name FROM officers WHERE status='Approved' ORDER BY full_name""")

        employees = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "attendance_report.html",
            records=records,
            employees=employees
        )
    
    @app.route("/attendance_success")
    def attendance_success():
        return "<h2>Face Captured Successfully</h2>"
    
    @app.route("/logout_officer")
    def logout_officer():
        session.pop("officer",None)
        return redirect("/officer")
    

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out successfully.")
        return redirect("/")
    
