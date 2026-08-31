import { Card } from "../components";

// Layout placeholder only, matching docs/wireframes.md "Admin — manage". Section
// switching and real user/department/knowledge-base management are not built yet.
const SECTIONS = ["Users", "Departments", "Knowledge base", "Analytics", "Settings"];

const USERS = [
  { name: "A. Reddy", role: "Engineer", department: "SAP" },
  { name: "S. Ganesh", role: "Engineer", department: "Cloud" },
  { name: "R. K.", role: "Admin", department: "—" },
];

export default function AdminHome() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1>Admin</h1>
          <p>Manage users, departments, and the knowledge base.</p>
        </div>
      </div>

      <div className="admin-layout">
        <Card title="Sections">
          <ul className="section-list">
            {SECTIONS.map((section) => (
              <li key={section}>{section}</li>
            ))}
          </ul>
        </Card>
        <Card title="Users">
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Department</th>
              </tr>
            </thead>
            <tbody>
              {USERS.map((user) => (
                <tr key={user.name}>
                  <td className="ticket-table-subject">{user.name}</td>
                  <td>{user.role}</td>
                  <td>{user.department}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
