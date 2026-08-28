import "../../styles/InstructorDash.css";

function Card({ text, img, count }) {
  return (
    <div className="cards">
      <img src={img} style={{ width: "24px", height: "24px", objectFit: "contain" }} alt="" />
      <p>{text}</p>
      <h2>{count}</h2>
    </div>
  );
}

export default Card;