import pandas as pd
import exams
import utils


def main(data):
    year_term = data["year_term"]
    administration = data["administration"]
    window = data['window']

    cr_1_08_filename = f"data/{year_term}/1_08.csv"
    registrations_df = pd.read_csv(cr_1_08_filename)
    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "Grade",
        "senior?",
    ]
    registrations_df["senior?"] = registrations_df["Grade"].apply(lambda x: x == "12")

    ## drop inactivies
    registrations_df = registrations_df[registrations_df["Status"] == True]
    registrations_df = registrations_df[cols]

    ## exam_info
    exam_info_dict = exams.administration_dates_dict[administration]
    exam_info_df = pd.DataFrame(exam_info_dict).T.reset_index(names="ExamTitle")
    exam_info_df = exam_info_df.rename(columns={"ExamCode": "Course"})

    ## attach exam info to registrations
    registrations_df = registrations_df.merge(exam_info_df, on=["Course"], how="left")

    ## attach teacher_name for relevant exams
    culminating_courses = []
    for course in exam_info_df["Course"].unique():
        if exams.culimating_course_dict.get(course):
            culminating_courses.extend(exams.culimating_course_dict.get(course))

    cr_1_01_filename = f"data/{year_term}/1_01.csv"
    enrollment_df = pd.read_csv(cr_1_01_filename)
    enrollment_df["Course"] = enrollment_df["Course"].apply(lambda x: x[0:5])
    enrollment_df = enrollment_df[enrollment_df["Course"].isin(culminating_courses)]
    enrollment_df["Course"] = enrollment_df["Course"].apply(
        lambda x: exams.culimating_course_to_exam_dict.get(x)
    )
    enrollment_df = enrollment_df.drop_duplicates(subset=["StudentID", "Course"])
    enrollment_df["Teacher"] = enrollment_df["Teacher1"].apply(
        lambda x: x.split(" ")[0]
    )
    cols = ["StudentID", "Course", "Teacher"]
    enrollment_df = enrollment_df[cols]

    registrations_df = registrations_df.merge(
        enrollment_df, on=["StudentID", "Course"], how="left"
    ).fillna("")

    ## attach testing accommodations info
    testing_accommodations_filename = f"data/{year_term}/testing_accommodations.csv"
    testing_accommodations_df = pd.read_csv(testing_accommodations_filename)
    testing_accommodations_df = testing_accommodations_df.drop_duplicates(
        keep="first", subset=["StudentID"]
    )
    testing_accommodations_df["SWD?"] = testing_accommodations_df["Grouping"].apply(
        lambda x: x in ["HSFI", "D75", "504s"]
    )
    testing_accommodations_df["D75?"] = testing_accommodations_df["Grouping"].apply(
        lambda x: x in ["D75"]
    )
    condition_cols = [
        "StudentID",
        "SWD?",
        "D75?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "one_on_one?",
        "Technology?",
        "large_print?",
    ]
    testing_accommodations_df = testing_accommodations_df[condition_cols]

    registrations_df = registrations_df.merge(
        testing_accommodations_df, on=["StudentID"], how="left"
    ).fillna(False)

    ## attach number of exams students are taking per day and flag potential conflicts

    num_of_exams_by_student_by_day = pd.pivot_table(
        registrations_df,
        index=["StudentID", "Day"],
        columns=["Time"],
        values="Course",
        aggfunc="count",
    ).fillna(0)
    num_of_exams_by_student_by_day["Total"] = num_of_exams_by_student_by_day.sum(axis=1)
    num_of_exams_by_student_by_day.columns = [
        f"{col}_#_of_exams_on_day" for col in num_of_exams_by_student_by_day.columns
    ]
    num_of_exams_by_student_by_day["Conflict?"] = num_of_exams_by_student_by_day[
        "Total_#_of_exams_on_day"
    ].apply(lambda x: x > 1)

    num_of_exams_by_student_by_day = num_of_exams_by_student_by_day.reset_index()
    print(num_of_exams_by_student_by_day)

    registrations_df = registrations_df.merge(
        num_of_exams_by_student_by_day, on=["StudentID", "Day"], how="left"
    ).fillna(0)

    ## flag double time students with multiple exams on a day
    double_time_multiple_exams = registrations_df[
        registrations_df["double_time?"]
        & (registrations_df["Total_#_of_exams_on_day"] > 1)
    ]
    if len(double_time_multiple_exams):
        double_time_multiple_exams_filename = (
            f"output/{year_term}/double_time_multiple_exams.xlsx"
        )
        double_time_multiple_exams.to_excel(
            double_time_multiple_exams_filename, index=False
        )

    ## output sections needed
    flags_cols = [
        "senior?",
        "SWD?",
        "D75?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "one_on_one?",
        "Technology?",
        "large_print?",
        "Conflict?",
    ]

    sections_df = (
        registrations_df[flags_cols].drop_duplicates().sort_values(by=flags_cols)
    )
    sections_df["Section"] = sections_df.apply(utils.return_section_number, axis=1)
    sections_df.to_excel("output/sections.xlsx")

    ## attach default_section_number
    registrations_df = registrations_df.merge(sections_df, on=flags_cols)

    ## number_of_students_per_section
    registrations_df["running_total"] = (
        registrations_df.sort_values(by=["Teacher", "LastName", "FirstName"])
        .groupby(["Course", "Section"])["StudentID"]
        .cumcount()
        + 1
    )

    ## adjust sections based on enrollment



    registrations = []
    for (exam, section), exam_section_df in registrations_df.groupby(
        ["Course", "Section"]
    ):
        if section < 18 or section in [20, 25,30,35]:
            max_capacity = utils.return_gen_ed_section_capacity(exam, window)
        else:
            max_capacity = 15

        current_capacity = len(exam_section_df)

        if current_capacity <= max_capacity:
            for index, student in exam_section_df.iterrows():
                student["NewSection"] = section
                registrations.append(student)
        else:
            current_capacity = 1
            # current_section = section - 1
            current_section = section

            for teacher, teacher_df in exam_section_df.groupby("Teacher"):
                for index, student in teacher_df.iterrows():
                    if current_capacity < max_capacity:
                        current_capacity += 1
                        section = current_section
                    else:
                        current_capacity = 1
                        current_section += 1

                    student["NewSection"] = section
                    registrations.append(student)
                if teacher == "":
                    pass
                else:
                    if current_section < 19:
                        current_section += 1

    registrations_df = pd.DataFrame(registrations)

    registrations_pvt_tbl = pd.pivot_table(
        registrations_df,
        index=["Course", "NewSection", "Teacher"],
        values="StudentID",
        aggfunc="count",
    )

    output_filename = "output/registrations.xlsx"
    writer = pd.ExcelWriter(output_filename)
    registrations_df = registrations_df.sort_values(
        by=['Day','Time',"Course", "NewSection"]
    )
    registrations_df.to_excel(writer, sheet_name="registrations")
    registrations_pvt_tbl.to_excel(writer, sheet_name="pivot")

    registrations_df['Action'] = 'Replace'
    registrations_df['GradeLevel'] = ''
    registrations_df['OfficialClass'] = ''
    stars_upload_cols = [
        'StudentID',
        'LastName',
        'FirstName',
        'GradeLevel',
        'OfficialClass',
        'Course',
        'NewSection',
        'Action',
    ]
    registrations_df[stars_upload_cols].to_excel(writer, sheet_name="STARS")
    students_taking_exams_lst = registrations_df['StudentID'].unique()
    
    accommodations_to_check = testing_accommodations_df[testing_accommodations_df['StudentID'].isin(students_taking_exams_lst)]
    accommodations_to_check.to_excel(writer, sheet_name="AccommodationsToCheck")

    writer.close()

    return True


if __name__ == "__main__":
    data = {
        "year_term": "2023_1",
        "administration": "January2024",
        "window":'January',
    }
    main(data)
