/**
 *
 */
package org.teamfarce.mirch;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

import com.badlogic.gdx.math.Vector2;
import org.teamfarce.mirch.Entities.Clue;

import java.util.ArrayList;

/**
 * Tests the journal class
 * @author jacobwunwin
 *
 */
public class Journal_Test extends GameTest {
	@Test
	public void test_addClue(){
		Journal journal = new Journal();

		Clue clue = new Clue("Clue name", "Description", 0,0,"Axe.png");

		journal.addClue(clue);

		assertEquals(clue, journal.foundClues.get(0));

	}

	@Test
	public void test_getClues(){
		Journal journal = new Journal();
		ArrayList<Clue> cluesList = new ArrayList<>();

		Clue clue = new Clue("Clue name", "Description", 0,0,"Axe.png");
		Clue clue2 = new Clue("Clue name 2", "Description", 0,0,"Axe.png");

		journal.addClue(clue);
		journal.addClue(clue2);

		cluesList.add(clue);
		cluesList.add(clue2);

		assertEquals(cluesList, journal.foundClues);
	}
}
