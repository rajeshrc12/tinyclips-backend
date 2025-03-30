from app.config.settings import DATABASE_URL
import psycopg


def update_video(video_id: str, new_count: int, duration: float):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Use double quotes around "imageCount" to preserve case sensitivity
                query = 'UPDATE "Video" SET "imageCount" = %s, "duration" = %s WHERE id = %s'
                cur.execute(query, (new_count, duration, video_id))
                conn.commit()
                print(
                    f"Updated video {video_id} with imageCount = {new_count} duration = {duration}")

    except Exception as e:
        print("Error updating imageCount:", e)


def update_balance(user_id: str, charges: float):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = 'UPDATE "User" SET balance = balance + %s WHERE id = %s RETURNING balance'
                cur.execute(query, (charges, user_id))
                updated_balance = cur.fetchone()

                if updated_balance is None:
                    print(f"User {user_id} not found.")
                    return None

                conn.commit()
                print(
                    f"Deducted {charges} from user {user_id}. New balance: {updated_balance[0]}")
                return updated_balance[0]
    except Exception as e:
        print(f"Error updating balance for user {user_id}: {e}")
        return None
